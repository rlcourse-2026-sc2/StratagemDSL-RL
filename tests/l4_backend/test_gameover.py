"""Optional GameOver at terminal phases (`--gameover`): one game = one scored episode for
LLM agents through PySC2; off by default so MARL training maps keep running."""
import re
from pathlib import Path

from stratagemdsl import pipeline
from stratagemdsl.backend.galaxy import GalaxyLowerer
from stratagemdsl.debug.galaxy_vm import GalaxyVM
from stratagemdsl.frontend import parse_file

ROOT = Path(__file__).resolve().parents[2]
ARID = ROOT / "examples/petri/arid_besiege_wei.strat"


def _fire_body(galaxy: str, transition: str) -> str:
    start = galaxy.index(f"void gf_net_fire_{transition} () {{")
    return galaxy[start:galaxy.index("\n}\n", start)]


def test_off_by_default():
    g = GalaxyLowerer(parse_file(ARID)).emit()
    assert "GameOver" not in g and "gv_plan_game_ended" not in g


def test_terminals_end_the_game_with_the_right_winner():
    g = GalaxyLowerer(parse_file(ARID), gameover=True).emit()
    assert "bool gv_plan_game_ended;" in g
    won = _fire_body(g, "confirm")
    assert re.search(r"GameOver\(1, c_gameOverVictory, true, true\);\s*GameOver\(2, c_gameOverDefeat", won)
    lost = _fire_body(g, "lose")
    assert re.search(r"GameOver\(2, c_gameOverVictory, true, true\);\s*GameOver\(1, c_gameOverDefeat", lost)
    assert g.count("GameOver(") == 6          # confirm, confirm_pincer, lose: two players each
    assert "if (gv_plan_game_ended == false)" in won


def _run(script):
    lo = GalaxyLowerer(parse_file(ARID), guard_oracle=True, gameover=True)
    vm = GalaxyVM(lo.emit())
    ends = []
    vm.natives["GameOver"] = lambda player, kind, dialog, score: ends.append(player)
    vm.boot()
    for tid, guards in script:
        trig = "gt_net_tick" if tid == "tick" else lo.transition_kinds[tid]["trigger"]
        for t in lo.net.transitions:
            if lo._uses_oracle(t):
                vm.globals[lo.net_name("guard", t.id)] = guards.get(t.id, False)
        vm.run_trigger(trig)
    return ends, vm.globals[lo.outcome_global]


def test_generated_galaxy_calls_gameover_once_per_episode():
    ends, outcome = _run([("rear_threat", {"rear_threat": True}), ("tick", {"lifted": True}),
                          ("spring", {"spring": True, "turn_back": True}), ("tick", {"confirm": True}),
                          ("tick", {"confirm_pincer": True, "lose": True})])
    assert outcome == 1 and ends == [1, 2]           # victory for 1 first, then defeat for 2; latched
    ends, outcome = _run([("tick", {"lose": True})])
    assert outcome == 2 and ends == [2, 1]


def test_pipeline_flag_and_note():
    lo = pipeline.lower(parse_file(ARID), gameover=True)
    assert "GameOver(1" in lo.galaxy
    assert any(n.startswith("gameover:") for n in lo.notes)
