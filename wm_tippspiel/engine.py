from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional, Tuple

GROUPS = list("ABCDEFGHIJKL")


@dataclass
class TeamObj:
    code: str
    name: str
    group_id: str
    group_pos: int
    fifa_rank: int


@dataclass
class MatchObj:
    match_no: int
    phase: str
    group_id: Optional[str]
    home_ref: Optional[str]
    away_ref: Optional[str]
    home_team_code: Optional[str]
    away_team_code: Optional[str]


@dataclass
class ResultObj:
    match_no: int
    home_goals: Optional[int] = None
    away_goals: Optional[int] = None
    winner_code: Optional[str] = None

    @property
    def has_score(self) -> bool:
        return self.home_goals is not None and self.away_goals is not None


@dataclass
class StandingRow:
    team: TeamObj
    played: int = 0
    won: int = 0
    drawn: int = 0
    lost: int = 0
    goals_for: int = 0
    goals_against: int = 0
    points: int = 0
    admin_required: bool = False

    @property
    def goal_diff(self) -> int:
        return self.goals_for - self.goals_against


@dataclass
class GroupTable:
    group_id: str
    rows: List[StandingRow]
    admin_required: bool = False
    note: str = ""


@dataclass
class BracketMatch:
    match_no: int
    phase: str
    home_ref: Optional[str]
    away_ref: Optional[str]
    home_code: Optional[str]
    away_code: Optional[str]
    winner_code: Optional[str] = None
    loser_code: Optional[str] = None


# FIFA Round-of-32 third-place slot constraints from Art. 12.6.
THIRD_PLACE_SLOTS = {
    "3ABCDF": {"match_no": 74, "winner_slot": "1E", "allowed": set("ABCDF")},
    "3CDFGH": {"match_no": 77, "winner_slot": "1I", "allowed": set("CDFGH")},
    "3CEFHI": {"match_no": 79, "winner_slot": "1A", "allowed": set("CEFHI")},
    "3EHIJK": {"match_no": 80, "winner_slot": "1L", "allowed": set("EHIJK")},
    "3BEFIJ": {"match_no": 81, "winner_slot": "1D", "allowed": set("BEFIJ")},
    "3AEHIJ": {"match_no": 82, "winner_slot": "1G", "allowed": set("AEHIJ")},
    "3EFGIJ": {"match_no": 85, "winner_slot": "1B", "allowed": set("EFGIJ")},
    "3DEIJL": {"match_no": 87, "winner_slot": "1K", "allowed": set("DEIJL")},
}


def _as_team_objs(teams: Iterable) -> Dict[str, TeamObj]:
    out = {}
    for t in teams:
        out[t.code] = TeamObj(t.code, t.name, t.group_id, t.group_pos, t.fifa_rank)
    return out


def _as_match_objs(matches: Iterable) -> List[MatchObj]:
    return [MatchObj(m.match_no, m.phase, m.group_id, m.home_ref, m.away_ref, m.home_team_code, m.away_team_code) for m in matches]


def _as_result_map(results: Iterable) -> Dict[int, ResultObj]:
    return {r.match_no: ResultObj(r.match_no, r.home_goals, r.away_goals, r.winner_code) for r in results}


def group_matches(matches: List[MatchObj], group_id: str) -> List[MatchObj]:
    return [m for m in matches if m.phase == "group" and m.group_id == group_id]


def _init_group_rows(teams: Dict[str, TeamObj], group_id: str) -> Dict[str, StandingRow]:
    return {
        t.code: StandingRow(team=t)
        for t in sorted(teams.values(), key=lambda x: x.group_pos)
        if t.group_id == group_id
    }


def _apply_match_to_rows(rows: Dict[str, StandingRow], home: str, away: str, hg: int, ag: int) -> None:
    h, a = rows[home], rows[away]
    h.played += 1; a.played += 1
    h.goals_for += hg; h.goals_against += ag
    a.goals_for += ag; a.goals_against += hg
    if hg > ag:
        h.won += 1; a.lost += 1; h.points += 3
    elif hg < ag:
        a.won += 1; h.lost += 1; a.points += 3
    else:
        h.drawn += 1; a.drawn += 1; h.points += 1; a.points += 1


def _head_to_head_values(codes: List[str], gm: List[MatchObj], result_map: Dict[int, ResultObj]) -> Dict[str, Tuple[int, int, int]]:
    points = {c: 0 for c in codes}
    gf = {c: 0 for c in codes}
    ga = {c: 0 for c in codes}
    code_set = set(codes)
    for m in gm:
        if m.home_team_code in code_set and m.away_team_code in code_set:
            r = result_map.get(m.match_no)
            if not r or not r.has_score:
                continue
            h, a = m.home_team_code, m.away_team_code
            gf[h] += r.home_goals; ga[h] += r.away_goals
            gf[a] += r.away_goals; ga[a] += r.home_goals
            if r.home_goals > r.away_goals:
                points[h] += 3
            elif r.home_goals < r.away_goals:
                points[a] += 3
            else:
                points[h] += 1; points[a] += 1
    return {c: (points[c], gf[c] - ga[c], gf[c]) for c in codes}


def _sort_tied_codes(codes: List[str], rows: Dict[str, StandingRow], gm: List[MatchObj], result_map: Dict[int, ResultObj]) -> Tuple[List[str], bool]:
    """Approximation of FIFA Art. 13 for scores-only mode.

    We implement the score-based criteria exactly enough for the app workflow:
    head-to-head points/GD/goals, then overall GD/goals. If teams remain tied
    after those score-based criteria, the app flags admin_required and uses the
    stored rank only as a deterministic display fallback. This is where the admin
    override is expected for live results.
    """
    admin_required = False
    h2h = _head_to_head_values(codes, gm, result_map)

    criteria = [
        lambda c: h2h[c][0],
        lambda c: h2h[c][1],
        lambda c: h2h[c][2],
        lambda c: rows[c].goal_diff,
        lambda c: rows[c].goals_for,
    ]

    remaining = codes[:]
    for keyfn in criteria:
        buckets: Dict[int, List[str]] = {}
        for c in remaining:
            buckets.setdefault(keyfn(c), []).append(c)
        if len(buckets) > 1:
            ordered = []
            for key in sorted(buckets.keys(), reverse=True):
                bucket = buckets[key]
                if len(bucket) > 1:
                    # Continue with following criteria inside this bucket.
                    sub, sub_admin = _sort_tied_codes_after(bucket, rows, gm, result_map, criteria[criteria.index(keyfn)+1:])
                    admin_required = admin_required or sub_admin
                    ordered.extend(sub)
                else:
                    ordered.extend(bucket)
            return ordered, admin_required

    # Not separable with score-only criteria. Use deterministic FIFA-rank fallback.
    admin_required = len(codes) > 1
    return sorted(codes, key=lambda c: rows[c].team.fifa_rank), admin_required


def _sort_tied_codes_after(codes: List[str], rows: Dict[str, StandingRow], gm: List[MatchObj], result_map: Dict[int, ResultObj], criteria) -> Tuple[List[str], bool]:
    for idx, keyfn in enumerate(criteria):
        buckets: Dict[int, List[str]] = {}
        for c in codes:
            buckets.setdefault(keyfn(c), []).append(c)
        if len(buckets) > 1:
            ordered = []
            admin = False
            for key in sorted(buckets.keys(), reverse=True):
                bucket = buckets[key]
                if len(bucket) > 1:
                    sub, sub_admin = _sort_tied_codes_after(bucket, rows, gm, result_map, criteria[idx+1:])
                    admin = admin or sub_admin
                    ordered.extend(sub)
                else:
                    ordered.extend(bucket)
            return ordered, admin
    return sorted(codes, key=lambda c: rows[c].team.fifa_rank), len(codes) > 1


def rank_group(group_id: str, teams: Dict[str, TeamObj], matches: List[MatchObj], result_map: Dict[int, ResultObj]) -> GroupTable:
    rows = _init_group_rows(teams, group_id)
    gm = group_matches(matches, group_id)
    for m in gm:
        r = result_map.get(m.match_no)
        if r and r.has_score and m.home_team_code and m.away_team_code:
            _apply_match_to_rows(rows, m.home_team_code, m.away_team_code, r.home_goals, r.away_goals)

    by_points: Dict[int, List[str]] = {}
    for code, row in rows.items():
        by_points.setdefault(row.points, []).append(code)

    ordered_codes: List[str] = []
    admin_required = False
    for pts in sorted(by_points.keys(), reverse=True):
        bucket = by_points[pts]
        if len(bucket) == 1:
            ordered_codes.extend(bucket)
        else:
            sub, sub_admin = _sort_tied_codes(bucket, rows, gm, result_map)
            admin_required = admin_required or sub_admin
            ordered_codes.extend(sub)

    ordered_rows = [rows[c] for c in ordered_codes]
    for r in ordered_rows:
        r.admin_required = admin_required
    return GroupTable(group_id=group_id, rows=ordered_rows, admin_required=admin_required, note="Admin-Korrektur empfohlen" if admin_required else "")


def compute_group_tables(teams_db, matches_db, results_db, overrides_db=None) -> Dict[str, GroupTable]:
    teams = _as_team_objs(teams_db)
    matches = _as_match_objs(matches_db)
    results = _as_result_map(results_db)
    tables = {g: rank_group(g, teams, matches, results) for g in GROUPS}

    overrides_by_group: Dict[str, Dict[str, int]] = {}
    if overrides_db:
        for o in overrides_db:
            overrides_by_group.setdefault(o.group_id, {})[o.team_code] = o.forced_rank

    for g, ranks in overrides_by_group.items():
        if g in tables and ranks:
            current = {row.team.code: row for row in tables[g].rows}
            forced = [current[c] for c, _rank in sorted(ranks.items(), key=lambda kv: kv[1]) if c in current]
            rest = [row for row in tables[g].rows if row.team.code not in ranks]
            tables[g].rows = forced + rest
            tables[g].admin_required = False
            tables[g].note = "Admin-Reihenfolge aktiv"
    return tables


def _best_thirds(tables: Dict[str, GroupTable]) -> List[StandingRow]:
    thirds = [tables[g].rows[2] for g in GROUPS]
    return sorted(thirds, key=lambda r: (-r.points, -r.goal_diff, -r.goals_for, r.team.fifa_rank))[:8]


def _assign_third_place_groups(best_thirds: List[StandingRow]) -> Dict[str, str]:
    """Assign the eight qualified third-placed teams to the FIFA R32 slots.

    The production-grade route is to replace this with the literal 495-row Annexe C
    lookup. For the prototype, this constraint solver picks a valid assignment using
    the official allowed-groups strings from Art. 12.6 and the computed order of the
    third-place table.
    """
    third_groups_ordered = [r.team.group_id for r in best_thirds]
    slot_order = ["3ABCDF", "3CDFGH", "3CEFHI", "3EHIJK", "3BEFIJ", "3AEHIJ", "3EFGIJ", "3DEIJL"]

    def backtrack(idx: int, used: set, assignment: Dict[str, str]) -> Optional[Dict[str, str]]:
        if idx == len(slot_order):
            return assignment.copy()
        slot = slot_order[idx]
        allowed = THIRD_PLACE_SLOTS[slot]["allowed"]
        candidates = [g for g in third_groups_ordered if g in allowed and g not in used]
        for g in candidates:
            assignment[slot] = g
            used.add(g)
            solved = backtrack(idx + 1, used, assignment)
            if solved:
                return solved
            used.remove(g)
            assignment.pop(slot, None)
        return None

    solved = backtrack(0, set(), {})
    if solved is None:
        # Should not happen with valid FIFA constraints; fail soft.
        solved = {}
    return solved


def _winner_loser(home: Optional[str], away: Optional[str], winner: Optional[str]) -> Tuple[Optional[str], Optional[str]]:
    if winner and winner == home:
        return winner, away
    if winner and winner == away:
        return winner, home
    return None, None


def build_bracket(teams_db, matches_db, results_db, overrides_db=None, picks_db=None) -> Tuple[Dict[int, BracketMatch], Dict[str, GroupTable], Dict[str, set]]:
    teams = _as_team_objs(teams_db)
    matches = {m.match_no: m for m in _as_match_objs(matches_db)}
    results = _as_result_map(results_db)
    picks = _as_result_map(picks_db or [])
    tables = compute_group_tables(teams_db, matches_db, results_db, overrides_db)

    qualifiers: Dict[str, str] = {}
    for g in GROUPS:
        qualifiers[f"1{g}"] = tables[g].rows[0].team.code
        qualifiers[f"2{g}"] = tables[g].rows[1].team.code
        qualifiers[f"3{g}"] = tables[g].rows[2].team.code

    best_thirds = _best_thirds(tables)
    third_slot_to_group = _assign_third_place_groups(best_thirds)
    for slot, group_id in third_slot_to_group.items():
        qualifiers[slot] = qualifiers[f"3{group_id}"]

    bracket: Dict[int, BracketMatch] = {}

    def resolve_ref(ref: Optional[str]) -> Optional[str]:
        if ref is None:
            return None
        if ref in qualifiers:
            return qualifiers[ref]
        if ref.startswith("W"):
            src = bracket.get(int(ref[1:]))
            return src.winner_code if src else None
        if ref.startswith("L"):
            src = bracket.get(int(ref[1:]))
            return src.loser_code if src else None
        if ref in teams:
            return ref
        return None

    for no in range(73, 105):
        m = matches.get(no)
        if not m:
            continue
        home = resolve_ref(m.home_ref)
        away = resolve_ref(m.away_ref)
        result_or_pick = results.get(no) or picks.get(no)
        winner = result_or_pick.winner_code if result_or_pick else None
        if winner not in {home, away}:
            winner = None
        win, loser = _winner_loser(home, away, winner)
        bracket[no] = BracketMatch(no, m.phase, m.home_ref, m.away_ref, home, away, win, loser)

    advancement = advancement_sets(bracket)
    return bracket, tables, advancement


def advancement_sets(bracket: Dict[int, BracketMatch]) -> Dict[str, set]:
    stages = {
        "r32": set(),
        "r16": set(),
        "qf": set(),
        "sf": set(),
        "final": set(),
        "champion": set(),
    }
    phase_to_stage = {"r32": "r32", "r16": "r16", "qf": "qf", "sf": "sf", "final": "final"}
    for bm in bracket.values():
        stage = phase_to_stage.get(bm.phase)
        if stage:
            if bm.home_code:
                stages[stage].add(bm.home_code)
            if bm.away_code:
                stages[stage].add(bm.away_code)
    final = bracket.get(104)
    if final and final.winner_code:
        stages["champion"].add(final.winner_code)
    return stages


def result_outcome(hg: int, ag: int) -> int:
    return 1 if hg > ag else -1 if hg < ag else 0
