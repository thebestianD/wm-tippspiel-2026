from __future__ import annotations

import os
import secrets
from datetime import datetime, timezone, timedelta
from typing import Optional
from zoneinfo import ZoneInfo

from dotenv import load_dotenv
from flask import Flask, flash, redirect, render_template, request, session, url_for
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError

from wm_tippspiel import db
from wm_tippspiel.models import ActualResult, AuditLog, GroupOverride, Match, Prediction, Setting, Team, User
from wm_tippspiel.seed_data import MATCH_INFO, seed_database, team_flag, team_flag_url
from wm_tippspiel.engine import build_bracket, compute_group_tables, result_outcome
from wm_tippspiel.scoring import score_user

load_dotenv()


def normalize_database_url(url: str | None) -> str:
    if not url:
        return "sqlite:///wm_tippspiel.db"
    # SQLAlchemy expects postgresql://; Supabase sometimes presents postgres://.
    if url.startswith("postgres://"):
        return "postgresql+psycopg://" + url[len("postgres://"):]
    if url.startswith("postgresql://"):
        return "postgresql+psycopg://" + url[len("postgresql://"):]
    return url


def create_app() -> Flask:
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", secrets.token_hex(32))
    app.config["SQLALCHEMY_DATABASE_URI"] = normalize_database_url(os.getenv("DATABASE_URL"))
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.init_app(app)

    with app.app_context():
        db.create_all()
        seed_database(db, __import__("wm_tippspiel.models", fromlist=["*"]))
        env_lock = os.getenv("PREDICTION_LOCK_AT")
        if env_lock:
            s = Setting.query.get("prediction_lock_at")
            if s:
                s.value = env_lock
            else:
                db.session.add(Setting(key="prediction_lock_at", value=env_lock))
            db.session.commit()

    register_routes(app)
    return app


def parse_lock_at() -> datetime:
    val = Setting.query.get("prediction_lock_at").value
    return datetime.fromisoformat(val.replace("Z", "+00:00"))


def predictions_locked() -> bool:
    return datetime.now(timezone.utc) >= parse_lock_at()


def current_user() -> Optional[User]:
    uid = session.get("user_id")
    if not uid:
        return None
    return User.query.get(uid)


def admin_required() -> bool:
    return bool(session.get("is_admin"))


HIDDEN_USER_SETTING_PREFIX = "hidden_user_"


def hidden_user_ids() -> set[int]:
    """Return users hidden from public leaderboards and overview pages."""
    rows = Setting.query.filter(
        Setting.key.like(f"{HIDDEN_USER_SETTING_PREFIX}%"),
        Setting.value == "1",
    ).all()

    result: set[int] = set()
    for row in rows:
        raw_id = row.key.removeprefix(HIDDEN_USER_SETTING_PREFIX)
        try:
            result.add(int(raw_id))
        except ValueError:
            continue
    return result


def set_user_hidden(user_id: int, hidden: bool) -> None:
    """Persist public visibility without changing or deleting the user's tips."""
    key = f"{HIDDEN_USER_SETTING_PREFIX}{user_id}"
    setting = Setting.query.get(key)

    if hidden:
        if setting:
            setting.value = "1"
        else:
            db.session.add(Setting(key=key, value="1"))
    elif setting:
        db.session.delete(setting)


def visible_users() -> list[User]:
    hidden_ids = hidden_user_ids()
    return [
        user
        for user in User.query.order_by(User.name).all()
        if user.id not in hidden_ids
    ]


def upsert_prediction(user_id: int, match_no: int, home_goals=None, away_goals=None, winner_code=None) -> None:
    p = Prediction.query.filter_by(user_id=user_id, match_no=match_no).first()
    if not p:
        p = Prediction(user_id=user_id, match_no=match_no)
        db.session.add(p)
    p.home_goals = home_goals
    p.away_goals = away_goals
    p.winner_code = winner_code


def upsert_actual(match_no: int, home_goals=None, away_goals=None, winner_code=None) -> None:
    r = ActualResult.query.filter_by(match_no=match_no).first()
    if not r:
        r = ActualResult(match_no=match_no)
        db.session.add(r)
    r.home_goals = home_goals
    r.away_goals = away_goals
    r.winner_code = winner_code


def parse_goal_value(raw: str | None, *, match_no: int, empty_as_zero: bool = False) -> int:
    """Parse and normalize a goal value. Accepts values like '02' as 2.

    If empty_as_zero=True, an empty field is interpreted as 0. This is used
    after we already checked that not both fields of a match are empty.
    """
    raw = "" if raw is None else raw.strip()
    if raw == "":
        if empty_as_zero:
            return 0
        raise ValueError(f"Leerer Wert bei Spiel {match_no}.")
    try:
        value = int(raw, 10)
    except ValueError as exc:
        raise ValueError(f"Ungültiges Ergebnis bei Spiel {match_no}.") from exc
    if value < 0 or value > 99:
        raise ValueError(f"Ungültiges Ergebnis bei Spiel {match_no}.")
    return value


def high_score_notice(match_nos: list[int]) -> str | None:
    if not match_nos:
        return None
    unique = sorted(set(match_nos))
    preview = ", ".join(f"M{no}" for no in unique[:8])
    if len(unique) > 8:
        preview += f" und {len(unique) - 8} weitere"
    return f"Hinweis: Bei {preview} wurde mindestens ein Wert von 10 oder mehr eingetragen. Bitte prüfe, ob das wirklich stimmt."


def format_lock_at_de(dt: datetime | None = None) -> str:
    """Format the lock timestamp for German users in Europe/Berlin time."""
    dt = dt or parse_lock_at()
    berlin = dt.astimezone(ZoneInfo("Europe/Berlin"))
    suffix = "MESZ" if berlin.dst() and berlin.dst().total_seconds() else "MEZ"
    return berlin.strftime("%d.%m.%Y %H:%M") + f" {suffix}"


def display_match_info(match_no: int) -> dict:
    """Return UI metadata for a match. Times are displayed in Germany/Berlin summer time."""
    raw = MATCH_INFO.get(match_no, {})
    label = "Termin offen"
    if raw.get("date_et") and raw.get("time_et"):
        # Tournament dates are in June/July, when ET=UTC-4 and Berlin=UTC+2.
        # FIFA publishes ET; Germany/Berlin display is +6h.
        dt = datetime.strptime(f"{raw['date_et']} {raw['time_et']}", "%Y-%m-%d %H:%M") + timedelta(hours=6)
        label = dt.strftime("%d.%m. %H:%M")
    return {
        "datetime_label": label,
        "broadcast": raw.get("broadcast", "Free-TV offen / MagentaTV"),
    }


def score_group_prediction(pred: Prediction | None, actual: ActualResult | None) -> dict | None:
    if not actual or actual.home_goals is None or actual.away_goals is None:
        return None
    if not pred or pred.home_goals is None or pred.away_goals is None:
        return {"points": 0, "class": "score-0", "label": "0 P"}
    if actual.home_goals == pred.home_goals and actual.away_goals == pred.away_goals:
        return {"points": 3, "class": "score-3", "label": "3 P"}
    if result_outcome(actual.home_goals, actual.away_goals) == result_outcome(pred.home_goals, pred.away_goals):
        if (actual.home_goals - actual.away_goals) == (pred.home_goals - pred.away_goals):
            return {"points": 2, "class": "score-2", "label": "2 P"}
        return {"points": 1, "class": "score-1", "label": "1 P"}
    return {"points": 0, "class": "score-0", "label": "0 P"}


def match_sort_key(match: Match) -> tuple[str, str, int]:
    raw = MATCH_INFO.get(match.match_no, {})
    return (raw.get("date_et") or "9999-12-31", raw.get("time_et") or "99:99", match.match_no)


def group_result_entered(match: Match, actual_by_no: dict[int, ActualResult]) -> bool:
    actual = actual_by_no.get(match.match_no)
    return bool(actual and actual.home_goals is not None and actual.away_goals is not None)


def ko_winner_entered(match: Match, actual_by_no: dict[int, ActualResult]) -> bool:
    actual = actual_by_no.get(match.match_no)
    return bool(actual and actual.winner_code)


def all_group_results_entered(matches: list[Match], actual_by_no: dict[int, ActualResult]) -> bool:
    group_matches = [m for m in matches if m.phase == "group"]
    if not group_matches:
        return False
    return all(group_result_entered(m, actual_by_no) for m in group_matches)


def apply_ko_scoring_gate(score: dict, ko_scoring_active: bool) -> dict:
    """Hide KO points defensively until all group results are entered by the admin."""
    if ko_scoring_active:
        return score

    guarded = dict(score)
    guarded["ko_points"] = 0
    guarded["total"] = guarded.get("group_points", 0)

    details = [
        detail
        for detail in guarded.get("details", [])
        if not (
            detail.startswith("R32:")
            or detail.startswith("R16:")
            or detail.startswith("QF:")
            or detail.startswith("SF:")
            or detail.startswith("FINAL:")
            or detail.startswith("CHAMPION:")
        )
    ]
    if "KO-Wertung noch nicht aktiv" not in details:
        details.append("KO-Wertung noch nicht aktiv")
    guarded["details"] = details
    return guarded


def format_tip(pred: Prediction | None) -> str:
    if not pred:
        return "–"
    if pred.home_goals is not None and pred.away_goals is not None:
        return f"{pred.home_goals}:{pred.away_goals}"
    if pred.winner_code:
        return pred.winner_code
    return "–"


KO_PHASES = [
    ("r32", "Sechzehntelfinale", list(range(73, 89))),
    ("r16", "Achtelfinale", list(range(89, 97))),
    ("qf", "Viertelfinale", list(range(97, 101))),
    ("sf", "Halbfinale", [101, 102]),
    ("final", "Finale", [104]),
]


GERMANY_STAGE_LABELS = [
    ("champion", "Weltmeister"),
    ("final", "Finale"),
    ("sf", "Halbfinale"),
    ("qf", "Viertelfinale"),
    ("r16", "Achtelfinale"),
    ("r32", "Sechzehntelfinale"),
]


def current_ko_stage(matches: list[Match], actual_by_no: dict[int, ActualResult]) -> dict:
    matches_by_no = {m.match_no: m for m in matches}

    for stage, label, match_nos in KO_PHASES:
        stage_matches = [matches_by_no[no] for no in match_nos if no in matches_by_no]
        if not stage_matches or not all(ko_winner_entered(m, actual_by_no) for m in stage_matches):
            return {"stage": stage, "label": label, "match_nos": match_nos}

    return {"stage": "champion", "label": "Weltmeister", "match_nos": [104]}


def build_live_group_context(users: list[User], matches: list[Match], actual_by_no: dict[int, ActualResult]) -> dict:
    group_matches = [m for m in matches if m.phase == "group"]
    completed = [m for m in group_matches if group_result_entered(m, actual_by_no)]
    open_matches = [m for m in group_matches if not group_result_entered(m, actual_by_no)]

    last_matches = sorted(completed, key=match_sort_key, reverse=True)[:3]
    next_matches = sorted(open_matches, key=match_sort_key)[:3]
    relevant_nos = [m.match_no for m in last_matches + next_matches]

    predictions = Prediction.query.filter(Prediction.match_no.in_(relevant_nos)).all() if relevant_nos else []
    pred_by_user_match = {(p.user_id, p.match_no): p for p in predictions}

    def rows_for_match(match: Match, scored: bool) -> list[dict]:
        rows = []
        actual = actual_by_no.get(match.match_no)
        for user in users:
            pred = pred_by_user_match.get((user.id, match.match_no))
            score = score_group_prediction(pred, actual) if scored else None
            rows.append({
                "user": user,
                "tip": format_tip(pred),
                "score": score,
            })
        return rows

    return {
        "mode": "group",
        "last_matches": [
            {"match": m, "actual": actual_by_no.get(m.match_no), "rows": rows_for_match(m, True)}
            for m in last_matches
        ],
        "next_matches": [
            {"match": m, "actual": None, "rows": rows_for_match(m, False)}
            for m in next_matches
        ],
    }


def build_live_ko_context(
    users: list[User],
    matches: list[Match],
    teams_db: list[Team],
    actuals: list[ActualResult],
    actual_by_no: dict[int, ActualResult],
    overrides: list[GroupOverride],
) -> dict:
    current = current_ko_stage(matches, actual_by_no)
    _actual_bracket, _actual_tables, actual_advancement = build_bracket(
        teams_db,
        matches,
        actuals,
        overrides_db=overrides,
    )
    correct_codes = actual_advancement.get(current["stage"], set())

    user_rows = []
    for user in users:
        user_preds = Prediction.query.filter_by(user_id=user.id).all()
        group_preds = [p for p in user_preds if p.match_no <= 72]
        ko_picks = [p for p in user_preds if p.match_no >= 73]
        _pred_bracket, _pred_tables, pred_advancement = build_bracket(
            teams_db,
            matches,
            group_preds,
            picks_db=ko_picks,
        )
        predicted_codes = sorted(pred_advancement.get(current["stage"], set()))
        user_rows.append({
            "user": user,
            "teams": [
                {"code": code, "correct": code in correct_codes}
                for code in predicted_codes
            ],
        })

    return {
        "mode": "ko",
        "stage": current["stage"],
        "stage_label": current["label"],
        "rows": user_rows,
    }


def user_profile_stats(
    user: User,
    matches: list[Match],
    teams_db: list[Team],
    actuals: list[ActualResult],
    actual_by_no: dict[int, ActualResult],
    overrides: list[GroupOverride],
    ko_scoring_active: bool,
) -> dict:
    predictions = Prediction.query.filter_by(user_id=user.id).all()
    pred_by_no = {p.match_no: p for p in predictions}
    group_predictions = [p for p in predictions if p.match_no <= 72]
    ko_predictions = [p for p in predictions if p.match_no >= 73]
    teams = {t.code: t for t in teams_db}

    group_pred_count = sum(
        1
        for p in group_predictions
        if p.home_goals is not None and p.away_goals is not None
    )
    champion_prediction = pred_by_no.get(104)
    champion_code = champion_prediction.winner_code if champion_prediction and champion_prediction.winner_code else None

    exact_matches = []
    for match in matches:
        if match.phase != "group":
            continue
        actual = actual_by_no.get(match.match_no)
        pred = pred_by_no.get(match.match_no)
        if not actual or not pred:
            continue
        if actual.home_goals is None or actual.away_goals is None:
            continue
        if pred.home_goals is None or pred.away_goals is None:
            continue
        if actual.home_goals == pred.home_goals and actual.away_goals == pred.away_goals:
            exact_matches.append({
                "match": match,
                "home": teams.get(match.home_team_code),
                "away": teams.get(match.away_team_code),
                "score": f"{actual.home_goals}:{actual.away_goals}",
                "info": display_match_info(match.match_no),
            })

    score = apply_ko_scoring_gate(score_user(user.id, overrides=overrides), ko_scoring_active)

    complete = bool(group_pred_count == 72 and champion_code)
    completeness_label = "Ja" if complete else "Nein"
    missing_parts = []
    if group_pred_count < 72:
        missing_parts.append(f"{72 - group_pred_count} Vorrundenspiele fehlen")
    if not champion_code:
        missing_parts.append("Weltmeistertipp fehlt")

    germany_stage = "Vorrunde"
    try:
        _pred_bracket, _pred_tables, pred_advancement = build_bracket(
            teams_db,
            matches,
            group_predictions,
            picks_db=ko_predictions,
        )
        for stage, label in GERMANY_STAGE_LABELS:
            if "GER" in pred_advancement.get(stage, set()):
                germany_stage = label
                break
    except Exception:
        # The profile should still render even if a user has not filled enough tips
        # to build a meaningful bracket yet.
        germany_stage = "Noch nicht bestimmbar"

    return {
        "score": score,
        "group_pred_count": group_pred_count,
        "complete": complete,
        "completeness_label": completeness_label,
        "missing_parts": missing_parts,
        "exact_matches": exact_matches,
        "champion_code": champion_code,
        "champion_team": teams.get(champion_code) if champion_code else None,
        "germany_stage": germany_stage,
    }


def register_routes(app: Flask) -> None:
    @app.context_processor
    def inject_globals():
        return {
            "app_name": os.getenv("APP_NAME", "WM 2026 Tippspiel"),
            "current_user": current_user(),
            "is_admin": admin_required(),
            "locked": predictions_locked,
            "lock_at": parse_lock_at,
            "lock_at_de": format_lock_at_de,
            "match_info": display_match_info,
            "team_flag": team_flag,
            "team_flag_url": team_flag_url,
        }

    @app.route("/")
    def index():
        user_count = len(visible_users())
        match_count = Match.query.count()
        return render_template("index.html", user_count=user_count, match_count=match_count)

    @app.route("/login", methods=["POST"])
    def login():
        name = (request.form.get("name") or "").strip()
        if not name:
            flash("Bitte einen Namen eingeben.", "error")
            return redirect(url_for("index"))
        user = User.query.filter_by(name=name).first()
        if not user:
            user = User(name=name, token=secrets.token_urlsafe(32))
            db.session.add(user)
            try:
                db.session.commit()
            except IntegrityError:
                db.session.rollback()
                user = User.query.filter_by(name=name).first()
        session["user_id"] = user.id
        flash(f"Eingeloggt als {user.name}.", "ok")
        return redirect(url_for("tips_group"))

    @app.route("/logout")
    def logout():
        session.pop("user_id", None)
        flash("Ausgeloggt.", "ok")
        return redirect(url_for("index"))

    @app.route("/tips/group", methods=["GET", "POST"])
    def tips_group():
        user = current_user()
        if not user:
            flash("Bitte zuerst einloggen.", "error")
            return redirect(url_for("index"))
        if request.method == "POST":
            if predictions_locked():
                flash("Die Tipps sind gesperrt. Änderungen sind nicht mehr möglich.", "error")
                return redirect(url_for("tips_group"))
            matches = Match.query.filter_by(phase="group").order_by(Match.match_no).all()
            high_score_matches = []
            for m in matches:
                hg_raw = request.form.get(f"hg_{m.match_no}")
                ag_raw = request.form.get(f"ag_{m.match_no}")
                if (hg_raw is None or hg_raw.strip() == "") and (ag_raw is None or ag_raw.strip() == ""):
                    continue
                try:
                    hg = parse_goal_value(hg_raw, match_no=m.match_no, empty_as_zero=True)
                    ag = parse_goal_value(ag_raw, match_no=m.match_no, empty_as_zero=True)
                except (ValueError, TypeError):
                    flash(f"Ungültiges Ergebnis bei Spiel {m.match_no}.", "error")
                    return redirect(url_for("tips_group"))
                if hg >= 10 or ag >= 10:
                    high_score_matches.append(m.match_no)
                upsert_prediction(user.id, m.match_no, hg, ag, None)
            db.session.add(AuditLog(action="prediction_group_update", details=f"user={user.name}"))
            db.session.commit()
            flash("Vorrunden-Tipps gespeichert.", "ok")
            notice = high_score_notice(high_score_matches)
            if notice:
                flash(notice, "warning")
            return redirect(url_for("tips_ko"))

        matches = Match.query.filter_by(phase="group").order_by(Match.match_no).all()
        preds_list = Prediction.query.filter_by(user_id=user.id).all()
        preds = {p.match_no: p for p in preds_list}
        teams_db = Team.query.all()
        teams = {t.code: t for t in teams_db}
        tables = compute_group_tables(teams_db, matches, preds_list)
        group_teams = {g: [{"code": t.code, "name": t.name, "rank": t.fifa_rank, "flag_url": team_flag_url(t.code)} for t in sorted(teams_db, key=lambda x: x.group_pos) if t.group_id == g] for g in "ABCDEFGHIJKL"}
        group_matches = {g: [{"no": m.match_no, "home": m.home_team_code, "away": m.away_team_code} for m in matches if m.group_id == g] for g in "ABCDEFGHIJKL"}
        return render_template("tips_group.html", matches=matches, preds=preds, teams=teams, tables=tables, group_teams=group_teams, group_matches=group_matches)

    @app.route("/tips/ko", methods=["GET", "POST"])
    def tips_ko():
        user = current_user()
        if not user:
            flash("Bitte zuerst einloggen.", "error")
            return redirect(url_for("index"))
        if request.method == "POST":
            if predictions_locked():
                flash("Die Tipps sind gesperrt. Änderungen sind nicht mehr möglich.", "error")
                return redirect(url_for("tips_ko"))
            teams = {t.code for t in Team.query.all()}
            for no in range(73, 105):
                winner = request.form.get(f"winner_{no}") or None
                if winner and winner in teams:
                    upsert_prediction(user.id, no, None, None, winner)
            db.session.add(AuditLog(action="prediction_ko_update", details=f"user={user.name}"))
            db.session.commit()
            flash("KO-Tipps gespeichert. Lade die Seite erneut bzw. speichere nach jeder Runde, bis der Weltmeister feststeht.", "ok")
            return redirect(url_for("tips_ko"))

        matches = Match.query.order_by(Match.match_no).all()
        teams_db = Team.query.all()
        preds = Prediction.query.filter_by(user_id=user.id).all()
        group_pred_count = Prediction.query.filter(Prediction.user_id == user.id, Prediction.match_no <= 72, Prediction.home_goals.isnot(None), Prediction.away_goals.isnot(None)).count()
        bracket, tables, advancement = build_bracket(teams_db, matches, [p for p in preds if p.match_no <= 72], picks_db=[p for p in preds if p.match_no >= 73])
        teams = {t.code: t for t in teams_db}
        pred_by_no = {p.match_no: p for p in preds}
        teams_json = {t.code: {"code": t.code, "name": t.name, "flag_url": team_flag_url(t.code)} for t in teams_db}
        bracket_json = {str(no): {
            "match_no": no,
            "phase": bm.phase,
            "home_ref": bm.home_ref,
            "away_ref": bm.away_ref,
            "home_code": bm.home_code,
            "away_code": bm.away_code,
            "winner_code": pred_by_no.get(no).winner_code if pred_by_no.get(no) else bm.winner_code,
            "meta": display_match_info(no),
        } for no, bm in bracket.items()}
        return render_template("tips_ko.html", bracket=bracket, teams=teams, pred_by_no=pred_by_no, group_pred_count=group_pred_count, tables=tables, teams_json=teams_json, bracket_json=bracket_json)

    @app.route("/admin/login", methods=["GET", "POST"])
    def admin_login():
        if request.method == "POST":
            password = request.form.get("password") or ""
            if password == os.getenv("ADMIN_PASSWORD", "admin"):
                session["is_admin"] = True
                flash("Admin-Login erfolgreich.", "ok")
                return redirect(url_for("admin"))
            flash("Falsches Admin-Passwort.", "error")
        return render_template("admin_login.html")

    @app.route("/admin/logout")
    def admin_logout():
        session.pop("is_admin", None)
        flash("Admin ausgeloggt.", "ok")
        return redirect(url_for("index"))

    @app.route("/admin", methods=["GET", "POST"])
    def admin():
        if not admin_required():
            return redirect(url_for("admin_login"))
        if request.method == "POST":
            action = request.form.get("action")
            if action == "save_results":
                high_score_matches = []
                for m in Match.query.order_by(Match.match_no).all():
                    if m.phase == "group":
                        hg_raw = request.form.get(f"actual_hg_{m.match_no}")
                        ag_raw = request.form.get(f"actual_ag_{m.match_no}")
                        if (hg_raw is None or hg_raw.strip() == "") and (ag_raw is None or ag_raw.strip() == ""):
                            continue
                        try:
                            hg = parse_goal_value(hg_raw, match_no=m.match_no, empty_as_zero=True)
                            ag = parse_goal_value(ag_raw, match_no=m.match_no, empty_as_zero=True)
                        except (ValueError, TypeError):
                            flash(f"Ungültiges Ergebnis bei Spiel {m.match_no}.", "error")
                            return redirect(url_for("admin"))
                        if hg >= 10 or ag >= 10:
                            high_score_matches.append(m.match_no)
                        upsert_actual(m.match_no, hg, ag, None)
                    else:
                        winner = request.form.get(f"actual_winner_{m.match_no}") or None
                        if winner:
                            upsert_actual(m.match_no, None, None, winner)
                db.session.add(AuditLog(action="admin_results_update", details="manual results saved"))
                db.session.commit()
                flash("Ergebnisse gespeichert.", "ok")
                notice = high_score_notice(high_score_matches)
                if notice:
                    flash(notice, "warning")
                return redirect(url_for("admin"))

            if action == "set_user_visibility":
                try:
                    user_id = int(request.form.get("user_id", ""))
                except ValueError:
                    flash("Ungültige Spieler-ID.", "error")
                    return redirect(url_for("admin"))

                user = User.query.get(user_id)
                if not user:
                    flash("Spieler nicht gefunden.", "error")
                    return redirect(url_for("admin"))

                hide_user = request.form.get("hidden") == "1"
                set_user_hidden(user.id, hide_user)
                db.session.add(AuditLog(
                    action="admin_user_visibility",
                    details=f"user={user.name}; hidden={hide_user}",
                ))
                db.session.commit()

                if hide_user:
                    flash(f"{user.name} wird in öffentlichen Übersichten ausgeblendet.", "ok")
                else:
                    flash(f"{user.name} wird wieder in öffentlichen Übersichten angezeigt.", "ok")
                return redirect(url_for("admin"))

            if action == "save_overrides":
                reason = request.form.get("override_reason", "Admin-Korrektur")
                for group_id in "ABCDEFGHIJKL":
                    raw = (request.form.get(f"override_{group_id}") or "").strip().upper()
                    GroupOverride.query.filter_by(group_id=group_id).delete()
                    if raw:
                        codes = [c.strip() for c in raw.replace(";", ",").split(",") if c.strip()]
                        for idx, code in enumerate(codes, start=1):
                            db.session.add(GroupOverride(group_id=group_id, team_code=code, forced_rank=idx, reason=reason))
                db.session.add(AuditLog(action="admin_overrides_update", details=reason))
                db.session.commit()
                flash("Tabellen-Korrekturen gespeichert.", "ok")
                return redirect(url_for("admin"))

        matches = Match.query.order_by(Match.match_no).all()
        teams_db = Team.query.all()
        actuals = ActualResult.query.all()
        overrides = GroupOverride.query.order_by(GroupOverride.group_id, GroupOverride.forced_rank).all()
        tables = compute_group_tables(teams_db, matches, actuals, overrides)
        bracket, _tables2, advancement = build_bracket(teams_db, matches, actuals, overrides_db=overrides)
        teams = {t.code: t for t in teams_db}
        actual_by_no = {a.match_no: a for a in actuals}
        overrides_by_group = {}
        for o in overrides:
            overrides_by_group.setdefault(o.group_id, []).append(o.team_code)
        override_placeholders = {g: ",".join(row.team.code for row in tables[g].rows) for g in "ABCDEFGHIJKL"}
        group_teams = {g: [{"code": t.code, "name": t.name, "rank": t.fifa_rank, "flag_url": team_flag_url(t.code)} for t in sorted(teams_db, key=lambda x: x.group_pos) if t.group_id == g] for g in "ABCDEFGHIJKL"}
        group_matches = {g: [{"no": m.match_no, "home": m.home_team_code, "away": m.away_team_code} for m in matches if m.phase == "group" and m.group_id == g] for g in "ABCDEFGHIJKL"}
        teams_json = {t.code: {"code": t.code, "name": t.name, "flag_url": team_flag_url(t.code)} for t in teams_db}
        bracket_json = {str(no): {
            "match_no": no,
            "phase": bm.phase,
            "home_ref": bm.home_ref,
            "away_ref": bm.away_ref,
            "home_code": bm.home_code,
            "away_code": bm.away_code,
            "winner_code": actual_by_no.get(no).winner_code if actual_by_no.get(no) else bm.winner_code,
            "meta": display_match_info(no),
        } for no, bm in bracket.items()}
        admin_users = User.query.order_by(User.name).all()
        hidden_ids = hidden_user_ids()
        prediction_counts = dict(
            db.session.query(Prediction.user_id, func.count(Prediction.id))
            .group_by(Prediction.user_id)
            .all()
        )
        return render_template(
            "admin.html",
            matches=matches,
            teams=teams,
            actual_by_no=actual_by_no,
            tables=tables,
            bracket=bracket,
            overrides_by_group=overrides_by_group,
            override_placeholders=override_placeholders,
            group_teams=group_teams,
            group_matches=group_matches,
            teams_json=teams_json,
            bracket_json=bracket_json,
            admin_users=admin_users,
            hidden_user_ids=hidden_ids,
            prediction_counts=prediction_counts,
        )

    @app.route("/points")
    def points():
        settings = {s.key: s.value for s in Setting.query.all()}
        defaults = {
            "score_exact_group": 3,
            "score_outcome_group": 1,
            "score_goal_diff_bonus": 1,
            "score_reaches_r32": 1,
            "score_reaches_r16": 2,
            "score_reaches_qf": 3,
            "score_reaches_sf": 4,
            "score_reaches_final": 6,
            "score_champion": 10,
        }
        scoring = {key: int(settings.get(key, default)) for key, default in defaults.items()}
        return render_template("points.html", scoring=scoring)

    @app.route("/leaderboard")
    def leaderboard():
        users = visible_users()
        matches = Match.query.order_by(Match.match_no).all()
        teams_db = Team.query.all()
        teams = {t.code: t for t in teams_db}
        actuals = ActualResult.query.all()
        actual_by_no = {a.match_no: a for a in actuals}
        overrides = GroupOverride.query.order_by(GroupOverride.group_id, GroupOverride.forced_rank).all()

        ko_scoring_active = all_group_results_entered(matches, actual_by_no)

        rows = []
        for user in users:
            score = apply_ko_scoring_gate(score_user(user.id, overrides=overrides), ko_scoring_active)
            rows.append({"user": user, **score})

        rows.sort(key=lambda row: row["total"], reverse=True)

        if ko_scoring_active:
            live_context = build_live_ko_context(users, matches, teams_db, actuals, actual_by_no, overrides)
        else:
            live_context = build_live_group_context(users, matches, actual_by_no)

        return render_template(
            "leaderboard.html",
            rows=rows,
            live=live_context,
            teams=teams,
            actual_by_no=actual_by_no,
        )

    @app.route("/profile/<int:user_id>")
    def profile(user_id: int):
        user = User.query.get_or_404(user_id)
        viewer = current_user()
        if user.id in hidden_user_ids() and not admin_required() and (not viewer or viewer.id != user.id):
            flash("Dieses Profil ist derzeit nicht öffentlich sichtbar.", "warning")
            return redirect(url_for("leaderboard"))

        matches = Match.query.order_by(Match.match_no).all()
        teams_db = Team.query.all()
        teams = {t.code: t for t in teams_db}
        actuals = ActualResult.query.all()
        actual_by_no = {a.match_no: a for a in actuals}
        overrides = GroupOverride.query.order_by(GroupOverride.group_id, GroupOverride.forced_rank).all()
        ko_scoring_active = all_group_results_entered(matches, actual_by_no)

        stats = user_profile_stats(
            user,
            matches,
            teams_db,
            actuals,
            actual_by_no,
            overrides,
            ko_scoring_active,
        )

        return render_template(
            "profile.html",
            profile_user=user,
            stats=stats,
            teams=teams,
        )

    @app.route("/tables")
    def tables():
        teams_db = Team.query.all()
        teams = {t.code: t for t in teams_db}
        matches = Match.query.order_by(Match.match_no).all()
        actuals = ActualResult.query.all()
        actual_by_no = {a.match_no: a for a in actuals}
        overrides = GroupOverride.query.order_by(GroupOverride.group_id, GroupOverride.forced_rank).all()
        tables = compute_group_tables(teams_db, matches, actuals, overrides)

        user = current_user()
        pred_by_no = {}
        if user:
            pred_by_no = {p.match_no: p for p in Prediction.query.filter_by(user_id=user.id).all()}
        match_scores = {m.match_no: score_group_prediction(pred_by_no.get(m.match_no), actual_by_no.get(m.match_no)) for m in matches if m.phase == "group"}
        group_matches = {g: [m for m in matches if m.phase == "group" and m.group_id == g] for g in "ABCDEFGHIJKL"}
        return render_template("tables.html", tables=tables, group_matches=group_matches, actual_by_no=actual_by_no, pred_by_no=pred_by_no, match_scores=match_scores, teams=teams)


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 7860)), debug=True)
