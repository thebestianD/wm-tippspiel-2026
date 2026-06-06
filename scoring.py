from __future__ import annotations

from typing import Dict, List

from .engine import build_bracket, result_outcome
from .models import ActualResult, Match, Prediction, Setting, Team


def _settings() -> Dict[str, int]:
    rows = {s.key: s.value for s in Setting.query.all()}

    def geti(key: str, default: int) -> int:
        try:
            return int(rows.get(key, default))
        except ValueError:
            return default

    return {
        "exact": geti("score_exact_group", 3),
        "outcome": geti("score_outcome_group", 1),
        "gd_bonus": geti("score_goal_diff_bonus", 1),
        "r32": geti("score_reaches_r32", 1),
        "r16": geti("score_reaches_r16", 2),
        "qf": geti("score_reaches_qf", 3),
        "sf": geti("score_reaches_sf", 4),
        "final": geti("score_reaches_final", 6),
        "champion": geti("score_champion", 10),
    }


def _all_group_results_entered(matches: list[Match], actual_by_no: dict[int, ActualResult]) -> bool:
    """Return True only once every group-stage match has an admin-entered final score."""
    group_matches = [m for m in matches if m.phase == "group"]

    if not group_matches:
        return False

    for match in group_matches:
        actual = actual_by_no.get(match.match_no)
        if not actual:
            return False
        if actual.home_goals is None or actual.away_goals is None:
            return False

    return True


def score_user(user_id: int, overrides=None) -> Dict:
    cfg = _settings()

    matches = Match.query.order_by(Match.match_no).all()
    teams = Team.query.all()
    actuals = ActualResult.query.all()
    user_preds = Prediction.query.filter_by(user_id=user_id).all()

    actual_by_no = {a.match_no: a for a in actuals}
    pred_by_no = {p.match_no: p for p in user_preds}

    group_points = 0
    ko_points = 0
    details: List[str] = []

    # Vorrundenpunkte: nur für Spiele, bei denen der Admin ein Ergebnis eingetragen hat.
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

        pts = 0

        if actual.home_goals == pred.home_goals and actual.away_goals == pred.away_goals:
            pts = cfg["exact"]
        elif result_outcome(actual.home_goals, actual.away_goals) == result_outcome(pred.home_goals, pred.away_goals):
            pts = cfg["outcome"]
            if (actual.home_goals - actual.away_goals) == (pred.home_goals - pred.away_goals):
                pts += cfg["gd_bonus"]

        group_points += pts

        if pts:
            details.append(f"M{match.match_no}: {pts} P")

    # KO-Punkte erst aktivieren, wenn ALLE Gruppenspiele vom Admin eingetragen wurden.
    if not _all_group_results_entered(matches, actual_by_no):
        details.append("KO-Wertung noch nicht aktiv")
        return {
            "total": group_points,
            "group_points": group_points,
            "ko_points": 0,
            "details": details,
        }

    # Ab hier: alle Gruppenspiele sind eingetragen, also darf KO-Wertung greifen.
    actual_bracket, actual_tables, actual_advancement = build_bracket(
        teams,
        matches,
        actuals,
        overrides_db=overrides,
    )

    user_group_predictions = [p for p in user_preds if p.match_no <= 72]
    user_ko_predictions = [p for p in user_preds if p.match_no >= 73]

    pred_bracket, pred_tables, pred_advancement = build_bracket(
        teams,
        matches,
        user_group_predictions,
        picks_db=user_ko_predictions,
    )

    for stage, score_per_team in [
        ("r32", cfg["r32"]),
        ("r16", cfg["r16"]),
        ("qf", cfg["qf"]),
        ("sf", cfg["sf"]),
        ("final", cfg["final"]),
        ("champion", cfg["champion"]),
    ]:
        actual_teams = actual_advancement.get(stage, set())
        predicted_teams = pred_advancement.get(stage, set())

        correct_teams = sorted(predicted_teams & actual_teams)
        stage_points = len(correct_teams) * score_per_team

        ko_points += stage_points

        if stage_points:
            details.append(
                f"{stage.upper()}: {len(correct_teams)} Teams × {score_per_team} = {stage_points}"
            )

    total = group_points + ko_points

    return {
        "total": total,
        "group_points": group_points,
        "ko_points": ko_points,
        "details": details,
    }
