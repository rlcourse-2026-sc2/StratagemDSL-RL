"""
Regression tests for the v16-review findings (S01-S04): two leftover gaps
in earlier fixes (S01, S03) and two genuine new regressions the earlier
fixes themselves introduced (S02, S04).
"""

import re

from stratagemdsl.paths import compiler_root
from stratagemdsl.frontend.antlr_parser import parse_source
from stratagemdsl.backend.galaxy import lower_to_galaxy
from galaxy_mini_interp import GalaxyMiniState, run_block, extract_func_body_lines, eval_expr, extract_test_conds
from net_harness import Harness, dispatch_guard


COMPILER_ROOT = str(compiler_root())


def _simulate_spawn_and_init(galaxy: str) -> GalaxyMiniState:
    state = GalaxyMiniState()
    spawn = re.search(r"void gf_Spawn \(\) \{(.*?)\n\}", galaxy, re.S).group(1).split("\n")
    run_block(spawn, state)
    run_block(extract_func_body_lines(galaxy, "gt_MapInit_Func"), state)
    return state


JOIN_INITIAL_BOTH = """strategy join_initial_both_test {
  world {
    force enemy { side = "enemy"; role = "test"; }
    asset watcher { side = "ally"; role = "test"; }
  }
  initial { alive(enemy); alive(watcher); }
  intent { pattern Test; primary alive(watcher); success alive(watcher); failure not (alive(watcher)); }
  plan {
    start [left, right];
    phase left { purpose "l"; actors [enemy]; focus [watcher]; }
    phase right { purpose "r"; actors [enemy]; focus [watcher]; }
    join ready all;
    phase done { purpose "done"; actors [enemy]; focus [watcher]; do { hold(enemy); } terminal success; }
    transition a: left -> ready { when true; priority 10; }
    transition b: right -> ready { when true; priority 10; }
    transition tail: ready -> done { when true; priority 10; }
  }
  binding sc2 {
    enemy = unit_group(owner=2, unit_type="Zealot", count=2, spawn=point_id(1532430748));
    watcher = unit(owner=1, unit_type="Nexus", at=point_id(1963276538));
  }
}"""


def test_s01_all_join_with_two_initial_arrivals_still_fires_its_tail():
    """S01: BOTH inputs to an `all` join arrive during the initial settle;
    the join must release and its tail action must run exactly once."""
    h = Harness(JOIN_INITIAL_BOTH)
    assert h.marked == {"done"}
    assert h.vm.calls.get("UnitGroupIssueOrder", 0) == 1


COUNTER_UNARY_NEG = """strategy counter_unary_neg_test {
  world {
    force enemy { side = "enemy"; role = "test"; }
    asset watcher { side = "ally"; role = "test"; }
    region zone { role = "test"; }
  }
  initial { alive(enemy); alive(watcher); }
  intent { pattern Test; primary alive(watcher); success alive(watcher); failure not (alive(watcher)); }
  plan {
    start [wait];
    phase wait { purpose "wait"; actors [enemy]; focus [watcher]; }
    phase done { purpose "done"; actors [enemy]; focus [watcher]; terminal success; }
    transition finish: wait -> done {
      on unit_died(enemy);
      when (killed_in(enemy, zone) + (-(killed_in(enemy, zone))) == 0);
      priority 10;
    }
  }
  binding sc2 {
    enemy = unit_group(owner=2, unit_type="Zealot", count=1, spawn=point_id(1532430748));
    watcher = unit(owner=1, unit_type="Nexus", at=point_id(1963276538));
    zone = circle(center=point_id(1963276538), radius=8);
  }
}"""


def test_s02_unary_minus_keeps_the_event_adjustment_consistent():
    """S02: `x + (-x) == 0` must be true regardless of whether the current
    death is inside or outside the zone -- every occurrence of the counter
    in the expression must reflect the SAME event-adjusted state. Before
    the fix, unary minus was treated as "doesn't depend on the event" and
    fell back to reading the un-adjusted counter, disagreeing with the
    sibling occurrence that WAS adjusted."""
    galaxy, _ = lower_to_galaxy(parse_source(COUNTER_UNARY_NEG))
    guard = dispatch_guard(galaxy, "finish")
    assert "gv_killed_in_5_enemy_4_zone" in guard
    for rg_value in ("true", "false"):
        guard_sub = (
            guard
            .replace("DistanceBetweenPoints(UnitGetPosition(EventUnit()), PointFromId(1963276538)) <= 8.0", rg_value)
            .replace("UnitGroupHasUnit(gv_enemy, EventUnit()) == true", "true")
            .replace("gv_phase_active_wait == true", "true")
        )
        state = GalaxyMiniState()
        state.globals["gv_killed_in_5_enemy_4_zone"] = 0
        assert eval_expr(guard_sub, state) is True


EVENT_PRIORITY = """strategy event_priority_test {
  world {
    force enemyA { side = "enemy"; role = "test"; }
    force enemyB { side = "enemy"; role = "test"; }
    force actor { side = "ally"; role = "test"; }
    region zone { role = "test"; }
  }
  initial { alive(enemyA); alive(enemyB); alive(actor); }
  intent { pattern Test; primary alive(actor); success alive(actor); failure not (alive(actor)); }
  plan {
    start [begin];
    phase begin { purpose "b"; actors [actor]; focus [actor]; }
    phase left { purpose "l"; actors [actor]; focus [actor]; terminal success; }
    phase right { purpose "r"; actors [actor]; focus [actor]; terminal failure; }
    transition to_left: begin -> left {
      on enter(enemyA, zone);
      when (count(enemyA) > 0);
      priority 20;
    }
    transition to_right: begin -> right {
      on enter(enemyA, zone);
      when (count(enemyB) > 0);
      priority 10;
    }
  }
  binding sc2 {
    enemyA = unit_group(owner=2, unit_type="Zealot", count=3, spawn=point_id(1532430748));
    enemyB = unit_group(owner=2, unit_type="Zealot", count=3, spawn=point_id(1532430764));
    actor = unit_group(owner=1, unit_type="Zealot", count=1, spawn=point_id(1963276538));
    zone = circle(center=point_id(1963276538), radius=8);
  }
}"""


def _run_event_priority_dispatcher(a_count: int, b_count: int) -> Harness:
    """One occurrence of enter(enemyA, zone): both transitions share the
    event, so one dispatcher snapshots them and fires by rank. The world
    guards count(enemyA) > 0 / count(enemyB) > 0 are driven through the
    harness's guard oracle."""
    h = Harness(EVENT_PRIORITY)
    h.event("to_left", to_left=a_count > 0, to_right=b_count > 0)
    return h


def test_s03_exactly_one_native_event_registration_for_the_shared_event():
    """T03 fix: assert the ACTUAL native call StratagemDSL emits for
    `on enter(F, R)` (TriggerAddEventUnitRegion), registered exactly once
    for the whole group -- not the wrong/guessed call names from the prior
    version of this test, and not an assertion with `or True` tacked on
    that could never fail."""
    galaxy, _ = lower_to_galaxy(parse_source(EVENT_PRIORITY))
    assert galaxy.count("TriggerAddEventUnitRegion") == 1


def test_s03_higher_priority_guard_wins_when_both_are_true():
    # to_right has priority 10 and its guard is also true -- it must win.
    assert _run_event_priority_dispatcher(a_count=5, b_count=5).marked == {"right"}


def test_s03_only_the_low_priority_guard_true_still_lets_it_fire():
    assert _run_event_priority_dispatcher(a_count=5, b_count=0).marked == {"left"}


def test_s03_neither_guard_true_leaves_begin_still_waiting():
    assert _run_event_priority_dispatcher(a_count=0, b_count=0).marked == {"begin"}


def test_s03_swapping_priority_on_same_event_transitions_changes_generated_code():
    swapped = EVENT_PRIORITY.replace("priority 20", "TMP").replace("priority 10", "priority 20").replace("TMP", "priority 10")
    g1, _ = lower_to_galaxy(parse_source(EVENT_PRIORITY))
    g2, _ = lower_to_galaxy(parse_source(swapped))
    assert g1 != g2, "swapping priority between two same-event siblings had no effect on the generated code"


TRIGGER_NAME_COLLISION = """strategy trigger_name_collision_test {
  world {
    force enemy { side = "enemy"; role = "test"; }
    asset watcher { side = "ally"; role = "test"; }
    region zone { role = "test"; }
  }
  initial { alive(enemy); alive(watcher); }
  intent { pattern Test; primary alive(watcher); success alive(watcher); failure not (alive(watcher)); }
  plan {
    start [wait, other];
    phase wait { purpose "w"; actors [enemy]; focus [watcher]; }
    phase other { purpose "o"; actors [enemy]; focus [watcher]; }
    phase done { purpose "d"; actors [enemy]; focus [watcher]; terminal success; }
    transition wait_done: wait -> done { when (count(enemy) > 0); priority 10; }
    transition poll_wait: other -> done { on leave(enemy, zone); priority 10; }
  }
  binding sc2 {
    enemy = unit_group(owner=2, unit_type="Zealot", count=2, spawn=point_id(1532430748));
    watcher = unit(owner=1, unit_type="Nexus", at=point_id(1963276538));
    zone = circle(center=point_id(1963276538), radius=8);
  }
}"""
