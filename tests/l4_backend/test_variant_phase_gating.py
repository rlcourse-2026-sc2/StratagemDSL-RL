
from stratagemdsl.paths import REPO_ROOT
from stratagemdsl.frontend import parse_file
from stratagemdsl.semantics.validator import Validator
from stratagemdsl.backend.galaxy import lower_to_galaxy
from net_harness import Harness


ROOT = REPO_ROOT


def _lower(name: str) -> str:
    s = parse_file(ROOT / 'tests/fixtures/variants' / name, 'lark')
    bag = Validator(s).validate()
    assert not bag.has_errors, [str(x) for x in bag.items]
    galaxy, _ = lower_to_galaxy(s)
    return galaxy


def test_deep_pull_phase_gating():
    """Each pull step only counts while its own phase holds the token."""
    _lower('dhls_deep_pull.strat')
    h = Harness(parse_file(ROOT / 'tests/fixtures/variants/dhls_deep_pull.strat', 'lark'))
    assert h.marked == {"first_stimulus"}
    assert h.event("midpoint_repull") == {"first_stimulus"}      # too early: no token in first_pull
    assert h.event("stimulus_pull") == {"first_pull"}
    assert h.event("deep_commitment") == {"first_pull"}          # still too early
    assert h.event("midpoint_repull") == {"deep_pull"}
    assert h.event("deep_commitment") == {"base_assault"}


def test_dual_corridor_first_branch_closes_choice_phase():
    """Both alternatives consume the single lure_choice token: the first one
    to fire closes the choice."""
    _lower('dhls_dual_corridor.strat')
    h = Harness(parse_file(ROOT / 'tests/fixtures/variants/dhls_dual_corridor.strat', 'lark'))
    assert h.event("choose_left") == {"left_pull"}
    assert h.event("choose_right") == {"left_pull"}
    assert h.event("left_committed") == {"exploit_left"}


def test_adcc_environment_projection():
    g = _lower('adcc_decoy_retarget.strat')
    # Enemy retarget is emitted.
    assert 'UnitGroupIssueOrder(gv_enemy_blockers' in g
    # Agent-side movement is deliberately not emitted as a concrete order.
    assert '// agent-controlled: move(...)' in g
