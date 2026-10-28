"""The LLM-PySC2 task bundle, the plan-driven simulator and the observed plan tracker (no StarCraft II needed)."""
import json
import math
from pathlib import Path

import pytest

from stratagemdsl import cli, paths
from stratagemdsl.frontend import parse_file
from stratagemdsl.packaging.terrain import load_profile
from stratagemdsl.play.game import Order
from stratagemdsl.play.llm_pysc2 import FORMAT, Projection, build_bundle
from stratagemdsl.play.plansim import PlanSim
from stratagemdsl.play.plantracker import PlanTracker
from stratagemdsl.play.scenario import build_scenario
from stratagemdsl.play.worldguards import evaluate, unsupported_calls

pytestmark = pytest.mark.skipif(
    not paths.stormlib_path().is_file() and paths.mpqeditor_path() is None,
    reason="no StormLib build for this system; set STORMLIB_PATH or MPQEDITOR_PATH")

ROOT = Path(__file__).resolve().parents[2]
ARID = ROOT / "examples/petri/arid_besiege_wei.strat"
LURE = ROOT / "examples/demos/cerulean_lure_zerg_vs_protoss.strat"


@pytest.fixture(scope="module")
def arid():
    return parse_file(ARID), load_profile(paths.base_maps_dir() / "arid_plateau.SC2Map")


@pytest.fixture(scope="module")
def lure():
    return parse_file(LURE), load_profile(paths.base_maps_dir() / "cerulean_fall_le.SC2Map")


# ------------------------------------------------------------------ bundle
def test_projection_matches_pysc2_minimap():
    p = Projection(72, 72, 64)
    assert p.to_minimap(0, 72) == [0, 0] and p.to_minimap(71.9, 0.1) == [63, 63]
    x, y = p.to_world(*p.to_minimap(52, 51))
    assert math.hypot(x - 52, y - 51) < 1.2


def test_bundle_carries_both_coordinate_systems(lure, tmp_path):
    strategy, profile = lure
    b = build_bundle(strategy, profile, tmp_path / "x.SC2Map", source=LURE)
    assert b["format"] == FORMAT and b["races"] == {"ally": "zerg", "enemy": "protoss"}
    assert [f["name"] for f in b["forces"] if f["controlled"]] == ["zergling_bait", "roach_strike"]
    lz = next(r for r in b["regions"] if r["name"] == "east_lure_zone")
    assert lz["world"] == [52.0, 51.0] and lz["minimap"] == Projection(72, 72).to_minimap(52, 51)
    plan = b["plan"]["force_plans"]["roach_strike"]
    assert [s["phase"] for s in plan] == ["deploy", "strike", "nexus_siege"]
    assert plan[0]["starts"] == "at the start" and "guard_pulled" in plan[1]["starts"]
    assert "minimap" in b["terrain"]["minimap"] and b["interface"]["raw_resolution"] == 72


def test_cli_builds_map_and_bundle(tmp_path):
    assert cli.main(["llm-pysc2", str(LURE), "-o", str(tmp_path)]) == 0
    bundle = json.loads((tmp_path / f"{LURE.stem}.llm_pysc2.json").read_text(encoding="utf-8"))
    assert Path(bundle["map"]["path"]).is_file() and bundle["map"]["gameover"] is True
    assert Path(bundle["source"]) == LURE.resolve()


# --------------------------------------------------------------- simulator
def test_oracle_plan_wins_arid(arid):
    strategy, profile = arid
    sim = PlanSim(strategy, profile, oracle=True, seed=0)
    f = sim.reset()
    while not f.done:
        f = sim.step([])
    assert f.result == "victory"
    fired = [t for h in sim.history for t in h["fired"]]
    assert fired.index("rear_threat") < fired.index("spring")
    assert "retarget(siege_force, raid_force)" in [o for h in sim.history for o in h["orders"]]


def test_without_allied_orders_the_siege_wins(arid):
    strategy, profile = arid
    sim = PlanSim(strategy, profile, seed=0)
    f = sim.reset()
    while not f.done:
        f = sim.step([])
    assert f.result == "defeat" and sim.count("besieged_base") == 0


def test_agent_orders_drive_the_script(lure):
    strategy, profile = lure
    sim = PlanSim(strategy, profile, seed=0)
    sim.reset()
    bait = [u.tag for u in sim.units if u.force == "zergling_bait"]
    lz = sim.regions["east_lure_zone"]
    sim.issue([Order("move", bait, point=(lz.x, lz.y))])
    for _ in range(200):
        sim.step([])
        if any(h["fired"] == ["bait_spotted"] for h in sim.history):
            break
    rec = next(h for h in sim.history if h["fired"] == ["bait_spotted"])
    assert rec["orders"] == ["move(protoss_guard, decoy_ground)"]
    # the enemy guard is invisible to the allied player until it comes close
    assert sim.visible_tags(1) >= set(bait)


def test_burrow_hides_a_unit(lure):
    strategy, profile = lure
    sim = PlanSim(strategy, profile, seed=0)
    sim.reset()
    roach = next(u for u in sim.units if u.unit_type == "Roach")
    sim.issue([Order("ability", [roach.tag], meta={"ability": "BurrowDown_quick"})])
    assert roach.unit_type == "RoachBurrowed" and roach.burrowed
    assert roach.tag not in sim.visible_tags(2)


# ------------------------------------------------------- guards and tracker
def test_world_guards_three_valued(arid):
    strategy, profile = arid
    sim = PlanSim(strategy, profile, seed=0)
    sim.reset()
    lose = next(t for t in strategy.plan.transitions if t.id == "lose")
    assert evaluate(lose.guard, {}, {}, sim) is False
    assert not unsupported_calls(lose.guard, {})

    class Blind:
        def count(self, name): return None
        def centroid(self, name): return None
        def count_in(self, name, region): return None
        def targeting(self, a, b): return None
        def killed_in(self, f, r): return None
        def seconds(self): return 0.0
        def elapsed(self, p): return None
    assert evaluate(lose.guard, {}, {}, Blind()) is None


def test_tracker_follows_the_script_from_one_side(lure):
    strategy, profile = lure
    sim = PlanSim(strategy, profile, oracle=True, seed=0)
    f = sim.reset()
    tracker = PlanTracker(strategy, build_scenario(strategy, profile))
    tracker.update(f, update_tracker=True)
    while not f.done:
        f = sim.step([])
        tracker.update(f, update_tracker=True)
    script = [t for h in sim.history for t in h["fired"]]
    seen = [t for h in tracker.history for t in h["fired"]]
    assert seen[:2] == script[:2] == ["bait_spotted", "guard_drawn_off"]
    assert "phases" in tracker.describe() or "active phases" in tracker.describe()


def test_play_dry_run_with_the_plan_simulator(tmp_path):
    from stratagemdsl.pipeline import run
    out = tmp_path / "map"
    r = run(ARID, until="pack", out_dir=out, gameover=True)
    assert r.ok
    rc = cli.main(["play", str(ARID), "--map", str(out / f"{ARID.stem}.SC2Map"), "--agent", "direct", "--dry-run",
                   "--sim", "plan", "--max-minutes", "2", "-o", str(tmp_path / "play")])
    assert rc == 0
    summary = json.loads((tmp_path / "play" / "summary.json").read_text(encoding="utf-8"))
    assert summary["episodes"] == 1 and sum(summary["results"].values()) == 1
