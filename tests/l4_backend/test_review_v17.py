"""
Regression tests for the v17-review findings T01 (P1: same incoming edge
double-counted when a plain phase is reachable via two distinct static
paths within one synchronous pass) and T02 (P2: name-collision avoidance
gaps beyond the original S04 case -- reserved MapInit/Reset names, cross
variable/function-name collisions, and ambiguous counter-name
concatenation).
"""

import re

from stratagemdsl.paths import compiler_root
from stratagemdsl.frontend.antlr_parser import parse_source
from stratagemdsl.backend.galaxy import lower_to_galaxy
from galaxy_mini_interp import GalaxyMiniState, run_block, extract_func_body_lines
from net_harness import Harness


COMPILER_ROOT = str(compiler_root())


def _simulate_spawn_and_init(galaxy: str) -> GalaxyMiniState:
    state = GalaxyMiniState()
    spawn = re.search(r"void gf_Spawn \(\) \{(.*?)\n\}", galaxy, re.S).group(1).split("\n")
    run_block(spawn, state)
    run_block(extract_func_body_lines(galaxy, "gt_MapInit_Func"), state)
    return state


JOIN_DUPLICATE_ARRIVAL = """strategy join_duplicate_arrival_test {
  world {
    force enemy { side = "enemy"; role = "test"; }
    asset watcher { side = "ally"; role = "test"; }
    region zone { role = "test"; }
  }
  initial { alive(enemy); alive(watcher); }
  intent { pattern Test; primary alive(watcher); success alive(watcher); failure not (alive(watcher)); }
  plan {
    start [a, b, blocked];
    phase a { purpose "a"; actors [enemy]; focus [watcher]; }
    phase b { purpose "b"; actors [enemy]; focus [watcher]; }
    phase blocked { purpose "blocked"; actors [enemy]; focus [watcher]; }
    join pass any;
    phase middle { purpose "middle"; actors [enemy]; focus [watcher]; }
    join ready all;
    phase done { purpose "done"; actors [enemy]; focus [watcher]; do { hold(enemy); } terminal success; }
    transition a_to_middle: a -> middle { when true; priority 10; }
    transition b_to_pass: b -> pass { when true; priority 10; }
    transition pass_to_middle: pass -> middle { when true; priority 10; }
    transition middle_ready: middle -> ready { when true; priority 10; }
    transition blocked_ready: blocked -> ready { on enter(enemy, zone); priority 10; }
    transition tail: ready -> done { when true; priority 10; }
  }
  binding sc2 {
    enemy = unit_group(owner=2, unit_type="Zealot", count=2, spawn=point_id(1532430748));
    watcher = unit(owner=1, unit_type="Nexus", at=point_id(1963276538));
    zone = circle(center=point_id(1963276538), radius=8);
  }
}"""


def test_t01_phase_reachable_via_two_static_paths_only_fires_its_outgoing_edge_once():
    """T01: `middle` is reached via TWO static paths in the same initial
    settle (directly from `a`, and via `b` -> the any-join `pass`). Its
    outgoing edge must fire ONCE: the second arrival at the once-phase
    `middle` is discarded, so the all-join sees one arrival, not two."""
    h = Harness(JOIN_DUPLICATE_ARRIVAL)
    assert h.tokens("ready.in.middle_ready") == 1
    assert "done" not in h.marked
    assert h.vm.calls.get("UnitGroupIssueOrder", 0) == 0
    assert h.event("blocked_ready") == {"done"}
    assert h.vm.calls.get("UnitGroupIssueOrder", 0) == 1


NAME_FUNCTION_CROSS_KIND = """strategy name_function_cross_kind_test {
  world {
    force f { side = "ally"; role = "test"; }
    force g { side = "ally"; role = "test"; }
    region zone_f { role = "test"; }
    region zone_g { role = "test"; }
  }
  initial { alive(f); alive(g); }
  intent { pattern Test; primary alive(f); success alive(f); failure not (alive(f)); }
  plan {
    start [begin1, begin2];
    phase begin1 { purpose "b1"; actors [f]; focus [f]; }
    phase begin2 { purpose "b2"; actors [g]; focus [g]; }
    phase done1 { purpose "d1"; actors [f]; focus [f]; terminal success; }
    phase done2 { purpose "d2"; actors [g]; focus [g]; terminal success; }
    transition hit: begin1 -> done1 { on enter(f, zone_f); priority 10; }
    transition hit_Func: begin2 -> done2 { on enter(g, zone_g); priority 10; }
  }
  binding sc2 {
    f = unit_group(owner=1, unit_type="Zealot", count=3, spawn=point_id(1532430748));
    g = unit_group(owner=1, unit_type="Zealot", count=3, spawn=point_id(1532430764));
    zone_f = circle(center=point_id(1532430748), radius=5);
    zone_g = circle(center=point_id(1532430764), radius=5);
  }
}"""

NAME_COUNTER_TUPLE = """strategy name_counter_tuple_test {
  world {
    force a_b { side = "enemy"; role = "test"; }
    force a { side = "enemy"; role = "test2"; }
    asset watcher { side = "ally"; role = "test"; }
    region c { role = "test"; }
    region b_c { role = "test2"; }
  }
  initial { alive(a_b); alive(a); alive(watcher); }
  intent { pattern Test; primary alive(watcher); success alive(watcher); failure not (alive(watcher)); }
  plan {
    start [wait1, wait2];
    phase wait1 { purpose "w1"; actors [a_b]; focus [watcher]; }
    phase wait2 { purpose "w2"; actors [a]; focus [watcher]; }
    phase done1 { purpose "d1"; actors [a_b]; focus [watcher]; terminal success; }
    phase done2 { purpose "d2"; actors [a]; focus [watcher]; terminal success; }
    transition t1: wait1 -> done1 { on unit_died(a_b); when (killed_in(a_b, c) >= 1); priority 10; }
    transition t2: wait2 -> done2 { on unit_died(a); when (killed_in(a, b_c) >= 1); priority 10; }
  }
  binding sc2 {
    a_b = unit_group(owner=2, unit_type="Zealot", count=1, spawn=point_id(1532430748));
    a = unit_group(owner=2, unit_type="Zealot", count=1, spawn=point_id(1532430764));
    watcher = unit(owner=1, unit_type="Nexus", at=point_id(1963276538));
    c = circle(center=point_id(1963276538), radius=8);
    b_c = circle(center=point_id(1963276538), radius=9);
  }
}"""
