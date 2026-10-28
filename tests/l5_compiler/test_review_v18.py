"""
Regression tests for the v18-review findings U01 (P1: a literal start
phase reachable from ANOTHER start phase loses its own tail cascade,
order-dependently) and U02 (P2: the naming registry didn't cover plain
`gv_*` globals -- entities, phase active/entered flags, join count/fired,
killed_in counters -- only `gt_*` triggers).
"""

import re
import tempfile
from pathlib import Path

from stratagemdsl.paths import compiler_root
from stratagemdsl.frontend.antlr_parser import parse_source
from stratagemdsl.compiler.galaxycc_adapter import compile_galaxy_source
from stratagemdsl.backend.galaxy import lower_to_galaxy


COMPILER_ROOT = str(compiler_root())


def _assert_globals_unique_and_compiles(strat_text: str):
    s = parse_source(strat_text)
    galaxy, _ = lower_to_galaxy(s)
    all_globals = re.findall(r"^(?:bool|int|unitgroup|region) (g[tv]_\w+);", galaxy, re.M)
    assert len(all_globals) == len(set(all_globals)), f"duplicate global declarations: {all_globals}"
    with tempfile.TemporaryDirectory() as tmp:
        result = compile_galaxy_source(galaxy, compiler_root=COMPILER_ROOT, source_path=str(Path(tmp) / "u02.galaxy"))
    assert result.judge_ok, result.judge_result


def test_u02_entity_named_like_an_internal_phase_entered_flag_does_not_collide():
    """A force literally named `phase_entered_wait` produces entity global
    `gv_phase_entered_wait` -- the exact same identifier an UNRELATED
    phase literally named `wait` derives for its own internal one-shot
    entry flag."""
    strat = """strategy u02_entered_test {
      world {
        force phase_entered_wait { side = "enemy"; role = "test"; }
        asset watcher { side = "ally"; role = "test"; }
      }
      initial { alive(phase_entered_wait); alive(watcher); }
      intent { pattern Test; primary alive(watcher); success alive(watcher); failure not (alive(watcher)); }
      plan {
        start [wait];
        phase wait { purpose "w"; actors [phase_entered_wait]; focus [watcher]; }
        phase done { purpose "d"; actors [phase_entered_wait]; focus [watcher]; terminal success; }
        transition finish: wait -> done { when (count(phase_entered_wait) > 0); priority 10; }
      }
      binding sc2 {
        phase_entered_wait = unit_group(owner=2, unit_type="Zealot", count=3, spawn=point_id(1532430748));
        watcher = unit(owner=1, unit_type="Nexus", at=point_id(1963276538));
      }
    }"""
    _assert_globals_unique_and_compiles(strat)


def test_u02_entity_named_like_an_internal_phase_active_flag_does_not_collide():
    strat = """strategy u02_active_test {
      world {
        force phase_active_wait { side = "enemy"; role = "test"; }
        asset watcher { side = "ally"; role = "test"; }
      }
      initial { alive(phase_active_wait); alive(watcher); }
      intent { pattern Test; primary alive(watcher); success alive(watcher); failure not (alive(watcher)); }
      plan {
        start [wait];
        phase wait { purpose "w"; actors [phase_active_wait]; focus [watcher]; }
        phase done { purpose "d"; actors [phase_active_wait]; focus [watcher]; terminal success; }
        transition finish: wait -> done { when (count(phase_active_wait) > 0); priority 10; }
      }
      binding sc2 {
        phase_active_wait = unit_group(owner=2, unit_type="Zealot", count=3, spawn=point_id(1532430748));
        watcher = unit(owner=1, unit_type="Nexus", at=point_id(1963276538));
      }
    }"""
    _assert_globals_unique_and_compiles(strat)


def test_u02_entity_named_like_a_killed_in_counter_does_not_collide():
    strat = """strategy u02_counter_test {
      world {
        force killed_in_5_enemy_4_zone { side = "enemy"; role = "test"; }
        force enemy { side = "enemy"; role = "test2"; }
        asset watcher { side = "ally"; role = "test"; }
        region zone { role = "test"; }
      }
      initial { alive(killed_in_5_enemy_4_zone); alive(enemy); alive(watcher); }
      intent { pattern Test; primary alive(watcher); success alive(watcher); failure not (alive(watcher)); }
      plan {
        start [wait1, wait2];
        phase wait1 { purpose "w1"; actors [killed_in_5_enemy_4_zone]; focus [watcher]; }
        phase wait2 { purpose "w2"; actors [enemy]; focus [watcher]; }
        phase done1 { purpose "d1"; actors [killed_in_5_enemy_4_zone]; focus [watcher]; terminal success; }
        phase done2 { purpose "d2"; actors [enemy]; focus [watcher]; terminal success; }
        transition t1: wait1 -> done1 { when (count(killed_in_5_enemy_4_zone) > 0); priority 10; }
        transition t2: wait2 -> done2 { on unit_died(enemy); when (killed_in(enemy, zone) >= 1); priority 10; }
      }
      binding sc2 {
        killed_in_5_enemy_4_zone = unit_group(owner=2, unit_type="Zealot", count=3, spawn=point_id(1532430748));
        enemy = unit_group(owner=2, unit_type="Zealot", count=1, spawn=point_id(1532430764));
        watcher = unit(owner=1, unit_type="Nexus", at=point_id(1963276538));
        zone = circle(center=point_id(1963276538), radius=8);
      }
    }"""
    _assert_globals_unique_and_compiles(strat)


DUPLICATE_START = """strategy duplicate_start_test {
  world {
    force enemy { side = "enemy"; role = "test"; }
    asset watcher { side = "ally"; role = "test"; }
    region zone { role = "test"; }
  }
  initial { alive(enemy); alive(watcher); }
  intent { pattern Test; primary alive(watcher); success alive(watcher); failure not (alive(watcher)); }
  plan {
    start [a, a, blocked];
    phase a { purpose "a"; actors [enemy]; focus [watcher]; }
    phase blocked { purpose "blocked"; actors [enemy]; focus [watcher]; }
    join ready all;
    phase done { purpose "done"; actors [enemy]; focus [watcher]; do { hold(enemy); } terminal success; }
    transition a_ready: a -> ready { when true; priority 10; }
    transition blocked_ready: blocked -> ready { on enter(enemy, zone); priority 10; }
    transition tail: ready -> done { when true; priority 10; }
  }
  binding sc2 {
    enemy = unit_group(owner=2, unit_type="Zealot", count=2, spawn=point_id(1532430748));
    watcher = unit(owner=1, unit_type="Nexus", at=point_id(1963276538));
    zone = circle(center=point_id(1963276538), radius=8);
  }
}"""
