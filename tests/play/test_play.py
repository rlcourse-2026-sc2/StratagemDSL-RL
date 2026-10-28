"""`stratagemdsl.play`: agents, observations and orders, on the toy simulator (no StarCraft II needed)."""
import json
import math
import os
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

from stratagemdsl import cli, paths
from stratagemdsl.frontend import parse_file
from stratagemdsl.packaging.terrain import load_profile
from stratagemdsl.play import agents, runner
from stratagemdsl.play.actions import MacroAction, parse_actions, to_orders
from stratagemdsl.play.llm import ScriptedDecider
from stratagemdsl.play.observe import ForceTracker
from stratagemdsl.play.pysc2_backend import raw_to_world, world_to_raw
from stratagemdsl.play.scenario import build_scenario
from stratagemdsl.play.toysim import ToySim

pytestmark = pytest.mark.skipif(
    not paths.stormlib_path().is_file() and paths.mpqeditor_path() is None,
    reason="no StormLib build for this system; set STORMLIB_PATH or MPQEDITOR_PATH")

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "examples/petri/arid_besiege_wei.strat"
BASE = paths.base_maps_dir() / "arid_plateau.SC2Map"


@pytest.fixture(scope="module")
def scenario():
    return build_scenario(parse_file(SRC), load_profile(BASE))


def test_scenario_reads_forces_regions_and_races(scenario):
    assert scenario.controlled == ["raid_force", "ambush_force"]
    assert (scenario.race("ally"), scenario.race("enemy")) == ("protoss", "zerg")
    siege = scenario.forces["siege_force"]
    assert siege.composition == [("Roach", 10), ("Zergling", 16)] and siege.count == 26 and siege.owner == 2
    assert scenario.forces["besieged_base"].kind == "asset"
    assert set(scenario.regions) == {"enemy_home_zone", "ambush_zone"}
    assert "siege_force" in scenario.targets("attack") and "besieged_base" not in scenario.targets("attack")


def test_tracker_matches_units_to_forces(scenario):
    sim = ToySim(scenario)
    tracker = ForceTracker(scenario)
    tracker.update(sim.reset())
    counts = {n: len(st.alive) for n, st in tracker.states.items()}
    assert counts == {"raid_force": 8, "ambush_force": 11, "besieged_base": 1, "siege_force": 26, "enemy_home": 1}
    assert max(tracker.calibration.values()) < 2 and tracker.calibration_problem() is None
    text = tracker.describe(sim._frame())
    assert "raid_force: 8/8 alive (8 Stalker)" in text and "on P4" in text
    assert "siege_force: 26 visible (10 Roach, 16 Zergling)" in text


def test_calibration_flags_a_flipped_frame(scenario):
    sim = ToySim(scenario)
    frame = sim.reset()
    for u in frame.units:
        u.y = scenario.profile.height - u.y        # what a missing y flip would look like
    tracker = ForceTracker(scenario)
    tracker.update(frame)
    assert "far from their spawn points" in tracker.calibration_problem()


def test_actions_are_validated(scenario):
    acts, errors = parse_actions([
        {"force": "raid_force", "action": "move", "target": "enemy_home_zone"},
        {"force": "siege_force", "action": "attack", "target": "besieged_base"},
        {"force": "ambush_force", "action": "fly", "target": "ambush_zone"},
        {"force": "ambush_force", "action": "attack", "target": "besieged_base"},
        {"force": "ambush_force", "action": "hold"}], scenario)
    assert [a.text() for a in acts] == ["move(raid_force, enemy_home_zone)", "hold(ambush_force)"]
    assert len(errors) == 3 and "not a force you command" in errors[0]


def test_orders_target_regions_structures_and_forces(scenario):
    sim = ToySim(scenario)
    tracker = ForceTracker(scenario)
    tracker.update(sim.reset())
    orders, notes = to_orders([MacroAction("raid_force", "move", "enemy_home_zone"),
                               MacroAction("raid_force", "attack", "enemy_home"),
                               MacroAction("ambush_force", "attack", "siege_force"),
                               MacroAction("ambush_force", "hold")], scenario, tracker)
    assert notes == []
    move, hit, chase, hold = orders
    assert move.kind == "move" and move.point == (60.5, 50.5) and len(move.tags) == 8
    assert hit.kind == "attack_unit" and hit.target_tag == tracker.states["enemy_home"].alive[0].tag
    assert chase.kind == "attack_pt" and math.hypot(chase.point[0] - 47, chase.point[1] - 17) < 2
    assert hold.kind == "hold" and len(hold.tags) == 11


def test_llm_agent_prompts_and_retries(scenario):
    decider = ScriptedDecider(["I would move the Stalkers.",
                               '{"orders": [{"force": "raid_force", "action": "move", "target": "enemy_home_zone"}]}'])
    agent = agents.LLMAgent(decider, with_plan=True)
    agent.reset(scenario, 4.0)
    sim = ToySim(scenario)
    tracker = ForceTracker(scenario)
    frame = sim.reset()
    tracker.update(frame)
    d = agent.decide(frame, tracker, [])
    assert [a.text() for a in d.actions] == ["move(raid_force, enemy_home_zone)"] and d.errors == []
    assert len(d.calls) == 2 and d.calls[0]["errors"]
    system, user = decider.prompts[0]
    assert "You win when: (alive(besieged_base) and defeated(siege_force))" in system
    assert "phase raid [raid_force (ally)]" in system and "on enter(siege_force, ambush_zone)" in system
    assert "Grid (rows" not in system and "R2: at (46.3, 46.3), joins P4 and P5" in system
    assert "point_xy" not in system
    assert "Your answer had problems" in decider.prompts[1][1]
    plain = agents.LLMAgent(ScriptedDecider([]))
    plain.reset(scenario, 4.0)
    assert "phase raid" not in plain.system


def test_episode_loop_logs_and_scores(scenario, tmp_path):
    zone = scenario.regions["enemy_home_zone"]

    def rule(frame):   # toy win condition: a Stalker reaches the Hatchery zone
        return "victory" if any(u.unit_type == "Stalker" and math.hypot(u.x - zone.x, u.y - zone.y) <= zone.radius
                                for u in frame.units) else None
    def answer(system, user):   # order the march whenever the Stalkers have no order yet
        if "- raid_force: none" in user:
            return ('{"orders": [{"force": "raid_force", "action": "move", "target": "enemy_home_zone"}],'
                    ' "note": "march on Daliang"}')
        return '{"orders": []}'
    decider = ScriptedDecider(answer)
    summary = runner.run(lambda: ToySim(scenario, rule=rule, max_loops=22 * 120), agents.LLMAgent(decider), scenario,
                         episodes=2, decision_seconds=4.0, out_dir=tmp_path, settings={"note": "test"})
    assert summary["results"] == {"victory": 2} and summary["win_rate"] == 1.0
    assert summary["win_rate_ci95"][0] > 0.3 and summary["mean_llm_calls"] >= 2
    episodes = [json.loads(line) for line in (tmp_path / "episodes.jsonl").read_text(encoding="utf-8").splitlines()]
    assert len(episodes) == 2 and episodes[0]["result"] == "victory"
    assert {"loop", "event", "force", "region"} <= set(next(e for e in episodes[0]["events"]
                                                           if e["force"] == "raid_force"))
    log = [json.loads(line) for line in (tmp_path / "episode_0.jsonl").read_text(encoding="utf-8").splitlines()]
    assert log[0]["type"] == "decision" and log[0]["actions"][0]["target"] == "enemy_home_zone"
    assert log[-1]["type"] == "end" and (tmp_path / "summary.json").is_file()


def test_direct_baseline_attacks_the_largest_enemy_force(scenario):
    assert agents.default_direct_orders(scenario) == ["raid_force:attack:siege_force", "ambush_force:attack:siege_force"]
    agent = agents.ScriptedAgent(["raid_force:move:ambush_zone"])
    agent.reset(scenario, 4.0)
    with pytest.raises(ValueError):
        agents.ScriptedAgent(["siege_force:move:ambush_zone"]).reset(scenario, 4.0)


def test_raw_coordinates_match_pysc2():
    assert raw_to_world(20, 13, 72) == (20.5, 58.5)
    assert world_to_raw(20.3, 58.7, 72) == pytest.approx((20.3, 13.3))
    # Against PySC2's own transforms, when it can be imported (Python <= 3.10, or patched).
    check = textwrap.dedent("""
        import random
        _s = random.shuffle
        random.shuffle = lambda x, r=None: _s(x)
        from pysc2.lib import actions, features, point
        aif = features.AgentInterfaceFormat(action_space=actions.ActionSpace.RAW, use_raw_units=True, raw_resolution=72)
        f = features.Features(aif, map_size=point.Point(72, 72))
        raw = f._world_to_minimap_px.fwd_pt(point.Point(20.3, 58.7))
        act = f.transform_action(None, actions.RAW_FUNCTIONS.Move_pt('now', [1], (20.3, 13.3)), skip_available=True)
        p = act.action_raw.unit_command.target_world_space_pos
        print(raw.x, raw.y, p.x, p.y)
    """)
    env = dict(os.environ, PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION="python")
    done = subprocess.run([sys.executable, "-c", check], capture_output=True, text=True, env=env)
    if done.returncode != 0:
        pytest.skip("PySC2 not importable here")
    rx, ry, wx, wy = map(float, done.stdout.split()[-4:])
    assert raw_to_world(rx, ry, 72) == (20.5, 58.5) and (wx, wy) == (20.5, 58.5)


def test_cli_dry_run_and_gameover_check(tmp_path, capsys):
    answers = tmp_path / "answers.txt"
    answers.write_text('{"orders": [{"force": "ambush_force", "action": "move", "target": "ambush_zone"}]}\n', encoding="utf-8")
    assert cli.main(["play", str(SRC), "--map", str(BASE), "--agent", "intents", "--dry-run", "--answers",
                     str(answers), "--max-minutes", "0.5", "-o", str(tmp_path / "run")]) == 0
    assert "intents: win rate 0.00" in capsys.readouterr().out
    summary = json.loads((tmp_path / "run" / "summary.json").read_text(encoding="utf-8"))
    assert summary["results"] == {"timeout": 1} and summary["settings"]["dry_run"] is True
    # a real run refuses a map that never ends the game
    assert cli.main(["play", str(SRC), "--map", str(BASE), "--agent", "direct", "-o", str(tmp_path / "x")]) == 1
    assert "never calls GameOver" in capsys.readouterr().out
