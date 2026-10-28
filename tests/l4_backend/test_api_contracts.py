"""Contract consistency and the actual strict guard -> Galaxy compiler path."""


from stratagemdsl.paths import REPO_ROOT
from stratagemdsl.frontend.antlr_parser import parse_file, parse_source
from stratagemdsl.backend.galaxy import GalaxyLowerer


ROOT = REPO_ROOT

PACKAGE = ROOT

DEMO = ROOT / "tests/fixtures/demos/jctq_api_contract_demo.strat"


def test_player_unit_count_uses_bound_owner_and_does_not_claim_visibility():
    s = parse_file(DEMO)
    lower = GalaxyLowerer(s)
    expr = parse_source(DEMO.read_text().replace("center_passable(exit_zone)",
                                               "player_unit_count(enemy_sentries) >= 1")).plan.transitions
    guard = next(t.guard for t in expr if t.id == 'approach_exit')
    emitted = lower.emit_expr(guard)
    assert 'UnitGroup(null, 2, RegionEntireMap()' in emitted
    assert 'VisIsVisibleForPlayer' not in emitted
