
from stratagemdsl.paths import REPO_ROOT
from stratagemdsl.frontend.lark_parser import parse_file
from stratagemdsl.semantics.validator import Validator
from stratagemdsl.backend.galaxy import lower_to_galaxy


ROOT = REPO_ROOT


def lower(name: str) -> str:
    s = parse_file(ROOT / "tests/fixtures/seeds" / f"{name}.strat")
    bag = Validator(s).validate()
    assert not bag.has_errors, [str(x) for x in bag.items]
    text, _ = lower_to_galaxy(s)
    return text


def test_wwjz_environment_projection():
    g = lower("wwjz")
    assert "TriggerAddEventUnitRegion(gt_rear_threat_causes_retarget" in g
    assert "UnitGroupHasUnit(gv_relief_force, EventUnit())" in g
    assert "OrderTargetingUnitGroup" in g
    assert "gv_enemy_siege_force" in g


def test_sdjx_does_not_control_allied_force():
    g = lower("sdjx")
    assert "// agent-controlled: move(...)" in g
    assert "OrderTargetingPoint(AbilityCommand(\"move\", 0), PointFromId(1887249362))" in g


def test_yqgz_counter_lowering():
    g = lower("yqgz")
    assert "gv_killed_in_14_zergling_force_10_tank_range" in g
    assert "gt_count_killed_in_14_zergling_force_10_tank_range" in g
    assert "AbilityCommand(\"Unsiege\", 0)" in g
    assert "gv_killed_in_14_zergling_force_10_tank_range + 1" in g
