"""The demos go through every layer, including map readback on their base maps."""
import pytest

from stratagemdsl import paths, pipeline

DEMOS = {  # name -> (base map, Galaxy fragments the demo must produce)
    "jctq_talv_queue_timeout": ("jctq_te.SC2Map", ("c_orderQueueAddToEnd", "GameGetMissionTime()",
                                "EventUnitTarget()", "libNtve_gf_KillingUnit()")),
    "jctq_api_contract_demo": ("jctq_te.SC2Map", ("PointPathingIsConnected(Point(",)),
    "cerulean_hellbat_raid": ("cerulean_fall_le.SC2Map", (
        'libNtve_gf_CreateUnitsWithDefaultFacing(4, "HellionTank", 0, 2, Point(42, 57));',
        'OrderTargetingUnitGroup(AbilityCommand("attack", 0), gv_zerg_hatchery)',
        "TriggerAddEventUnitDied(gt_Reset, null);")),
    "cerulean_lure_zerg_vs_protoss": ("cerulean_fall_le.SC2Map", (
        'UnitGroupIssueOrder(gv_protoss_guard, OrderTargetingPoint(AbilityCommand("move", 0), Point(66, 40))',
        "TriggerAddEventUnitRegion(gt_bait_spotted, null, gv_east_lure_zone, true);",
        'OrderTargetingUnitGroup(AbilityCommand("attack", 0), gv_roach_strike)')),
}


def _source(name):
    """Student-facing demos live in examples/demos; regression-only ones in tests/fixtures/demos."""
    path = paths.REPO_ROOT / "examples/demos" / f"{name}.strat"
    return path if path.exists() else paths.REPO_ROOT / "tests/fixtures/demos" / f"{name}.strat"


@pytest.mark.parametrize("name", sorted(DEMOS))
def test_demo_reaches_map_readback(name, tmp_path):
    r = pipeline.run(_source(name), until="pack", out_dir=tmp_path,
                     base_map=paths.base_maps_dir() / DEMOS[name][0])
    assert r.ok, (r.failed_stage, r.error)
    assert "PointFromId" not in r.galaxy
    for token in DEMOS[name][1]:
        assert token in r.galaxy, token
    assert r.map_result["status"] == "passed"
