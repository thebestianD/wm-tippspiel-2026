from types import SimpleNamespace

from wm_tippspiel.engine import compute_group_tables, build_bracket
from wm_tippspiel.seed_data import TEAMS, GROUP_MATCHES, KNOCKOUT_MATCHES


def mk_teams():
    return [SimpleNamespace(code=c, name=n, group_id=g, group_pos=p, fifa_rank=r) for c,n,g,p,r in TEAMS]


def mk_matches():
    ms = []
    for no,g,h,a in GROUP_MATCHES:
        ms.append(SimpleNamespace(match_no=no, phase="group", group_id=g, home_ref=h, away_ref=a, home_team_code=h, away_team_code=a))
    for no,phase,hr,ar in KNOCKOUT_MATCHES:
        ms.append(SimpleNamespace(match_no=no, phase=phase, group_id=None, home_ref=hr, away_ref=ar, home_team_code=None, away_team_code=None))
    return ms


def mk_result(no, hg, ag):
    return SimpleNamespace(match_no=no, home_goals=hg, away_goals=ag, winner_code=None)


def test_all_groups_have_four_teams():
    teams = mk_teams()
    for g in "ABCDEFGHIJKL":
        assert len([t for t in teams if t.group_id == g]) == 4


def test_group_table_basic_points():
    # In group A let Mexico win all games, Korea second.
    results = [
        mk_result(1, 2, 0),  # MEX-RSA
        mk_result(2, 1, 0),  # KOR-CZE
        mk_result(25, 1, 1),
        mk_result(28, 2, 1), # MEX-KOR
        mk_result(53, 0, 3), # CZE-MEX
        mk_result(54, 0, 2), # RSA-KOR
    ]
    tables = compute_group_tables(mk_teams(), mk_matches(), results)
    assert tables["A"].rows[0].team.code == "MEX"
    assert tables["A"].rows[1].team.code == "KOR"


def test_bracket_resolves_r32_when_group_scores_exist():
    # Every listed home team wins 1:0. This is synthetic but complete.
    results = [mk_result(no, 1, 0) for no, _g, _h, _a in GROUP_MATCHES]
    bracket, tables, adv = build_bracket(mk_teams(), mk_matches(), results)
    assert 73 in bracket
    assert bracket[73].home_code is not None
    assert bracket[73].away_code is not None
    assert len(adv["r32"]) == 32
