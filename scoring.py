from __future__ import annotations
from typing import Dict, List

from .engine import build_bracket, result_outcome
from .models import ActualResult, Match, Prediction, Setting, Team


ROUND_SCORE_KEYS = {
    "r32": "score_reaches_r32",
    "r16": "score_reaches_r16",
    "qf": "score_reaches_qf",
    "sf": "score_reaches_sf",
    "final": "score_reaches_final",
    "champion": "score_champion",
}


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
        **{stage: geti(key, default) for stage, key, default in [
            ("r32", "score_reaches_r32", 1),
            ("r16", "score_reaches_r16", 2),
            ("qf", "score_reaches_qf", 3),
            ("sf", "score_reaches_sf", 4),
            ("final", "score_reaches_final", 6),
            ("champion", "score_champion", 10),
        ]}
    }


def _all_group_results_entered(matches: list[Match], actual_by_no: dict[int, ActualResult]) -> bool:
    """KO points only become active once all group matches have final admin results."""
    group_matches = [m for m in matches if m.phase == "group"]
    if not group_matches:
        return False
    for m in group_matches:
        actual = actual_by_no.get(m.match_no)
        if not actual or actual.home_goals is None or actual.away_goals is None:
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

    for m in matches:
        if m.phase != "group":
            continue
        a = actual_by_no.get(m.match_no)
        p = pred_by_no.get(m.match_no)
        if not a or not p or a.home_goals is None or a.away_goals is None or p.home_goals is None or p.away_goals is None:
            continue
        pts = 0
        if a.home_goals == p.home_goals and a.away_goals == p.away_goals:
            pts += cfg["exact"]
        elif result_outcome(a.home_goals, a.away_goals) == result_outcome(p.home_goals, p.away_goals):
            pts += cfg["outcome"]
            if (a.home_goals - a.away_goals) == (p.home_goals - p.away_goals):
                pts += cfg["gd_bonus"]
        if pts:
            details.append(f"M{m.match_no}: {pts} P")
        group_points += pts

    if _all_group_results_entered(matches, actual_by_no):
        # Actual advancement comes from actual scores/results plus admin table overrides.
        _actual_bracket, _actual_tables, actual_adv = build_bracket(teams, matches, actuals, overrides_db=overrides)

        # User advancement comes from the user's group-score predictions and KO winner picks.
        user_group_score_preds = [p for p in user_preds if p.match_no <= 72]
        user_ko_picks = [p for p in user_preds if p.match_no >= 73]
        _pred_bracket, _pred_tables, pred_adv = build_bracket(teams, matches, user_group_score_preds, picks_db=user_ko_picks)

        for stage, score in [("r32", cfg["r32"]), ("r16", cfg["r16"]), ("qf", cfg["qf"]), ("sf", cfg["sf"]), ("final", cfg["final"]), ("champion", cfg["champion"])]:
            correct_teams = sorted(pred_adv.get(stage, set()) & actual_adv.get(stage, set()))
            stage_points = len(correct_teams) * score
            ko_points += stage_points
            if stage_points:
                details.append(f"{stage.upper()}: {len(correct_teams)} Teams × {score} = {stage_points}")
    else:
        details.append("KO-Wertung noch nicht aktiv")

    total = group_points + ko_points
    return {
        "total": total,
        "group_points": group_points,
        "ko_points": ko_points,
        "details": details,
    }
