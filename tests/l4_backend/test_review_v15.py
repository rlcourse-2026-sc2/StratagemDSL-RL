"""
Regression tests for the v15-review findings (R01-R05), using
_galaxy_mini_interp to actually EXECUTE the generated Galaxy code's
assignments/if-chains against a simulated globals dict, rather than
asserting on substrings of the generated text. A prior review correctly
pointed out that text-substring assertions can't distinguish correct
nesting/ordering from incorrect nesting/ordering that happens to mention
the same variable names.

v0.6: plan behaviour is checked by executing the generated token game in
debug.galaxy_vm next to the net simulator (net_harness.Harness); guard
expressions are still evaluated with galaxy_mini_interp.
"""

import re

from stratagemdsl.frontend.antlr_parser import parse_source
from stratagemdsl.backend.galaxy import lower_to_galaxy
from galaxy_mini_interp import GalaxyMiniState, run_block, extract_func_body_lines
from net_harness import Harness, dispatch_guard


def _simulate_spawn_and_init(galaxy: str) -> GalaxyMiniState:
    """Runs gf_Spawn() then gt_MapInit_Func()'s action body -- together
    these ARE what actually happens the instant the map starts, including
    the initial trivially-true cascade fold that lives in MapInit, not
    Spawn."""
    state = GalaxyMiniState()
    spawn = re.search(r"void gf_Spawn \(\) \{(.*?)\n\}", galaxy, re.S).group(1).split("\n")
    run_block(spawn, state)
    run_block(extract_func_body_lines(galaxy, "gt_MapInit_Func"), state)
    return state


def _fire(galaxy: str, state: GalaxyMiniState, trigger_func: str) -> None:
    run_block(extract_func_body_lines(galaxy, trigger_func), state)


JOIN_INITIAL_PARTIAL = """strategy join_initial_partial_test {
  world {
    force enemy { side = "enemy"; role = "test"; }
    asset watcher { side = "ally"; role = "test"; }
    region zone { role = "test"; }
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
    transition b: right -> ready { on leave(enemy, zone); priority 10; }
    transition tail: ready -> done { when true; priority 10; }
  }
  binding sc2 {
    enemy = unit_group(owner=2, unit_type="Zealot", count=2, spawn=point_id(1532430748));
    watcher = unit(owner=1, unit_type="Nexus", at=point_id(1963276538));
    zone = circle(center=point_id(1963276538), radius=8);
  }
}"""


def test_r01_join_reached_by_one_initial_instant_edge_does_not_prematurely_activate():
    """R01: `left` is a start phase with a trivially-true edge straight
    into an `all` join. Reaching the join via ONLY this one input at spawn
    must NOT activate the join or anything downstream of it."""
    h = Harness(JOIN_INITIAL_PARTIAL)
    assert h.tokens("ready.in.a") == 1
    assert h.marked == {"right"}
    assert h.vm.calls.get("UnitGroupIssueOrder", 0) == 0
    assert h.event("b") == {"done"}
    assert h.vm.calls.get("UnitGroupIssueOrder", 0) == 1


JOIN_ANY_REFIRES = """strategy join_any_refires_test {
  world {
    force enemy { side = "enemy"; role = "test"; }
    asset watcher { side = "ally"; role = "test"; }
    region left_zone { role = "test"; }
    region right_zone { role = "test"; }
  }
  initial { alive(enemy); alive(watcher); }
  intent { pattern Test; primary alive(watcher); success alive(watcher); failure not (alive(watcher)); }
  plan {
    start [left, right];
    phase left { purpose "l"; actors [enemy]; focus [watcher]; }
    phase right { purpose "r"; actors [enemy]; focus [watcher]; }
    join ready any;
    phase done { purpose "done"; actors [enemy]; focus [watcher]; do { hold(enemy); } terminal success; }
    transition a: left -> ready { on enter(enemy, left_zone); priority 10; }
    transition b: right -> ready { on leave(enemy, right_zone); priority 10; }
    transition tail: ready -> done { when true; priority 10; }
  }
  binding sc2 {
    enemy = unit_group(owner=2, unit_type="Zealot", count=2, spawn=point_id(1532430748));
    watcher = unit(owner=1, unit_type="Nexus", at=point_id(1963276538));
    left_zone = circle(center=point_id(1532430748), radius=5);
    right_zone = circle(center=point_id(1532430764), radius=5);
  }
}"""


def test_r02_join_any_does_not_refire_tail_on_a_later_arrival():
    """R02: an `any` join fires (and cascades through its tail) on the
    FIRST arrival. A SECOND, later arrival must not re-run the tail."""
    h = Harness(JOIN_ANY_REFIRES)
    assert "done" in h.event("a")
    assert h.vm.calls.get("UnitGroupIssueOrder", 0) == 1
    h.event("b")
    assert h.vm.calls.get("UnitGroupIssueOrder", 0) == 1, "tail action re-fired on a later any-policy arrival"
    assert h.tokens("ready.armed") == 0 and h.tokens("ready.arrivals") == 1


MIXED_PRIORITY = """strategy mixed_priority_test {
  world {
    force enemy { side = "enemy"; role = "test"; }
    force actor { side = "ally"; role = "test"; }
  }
  initial { alive(enemy); alive(actor); }
  intent { pattern Test; primary alive(actor); success alive(actor); failure not (alive(actor)); }
  plan {
    start [begin];
    phase begin { purpose "b"; actors [actor]; focus [actor]; }
    phase left { purpose "l"; actors [actor]; focus [actor]; terminal success; }
    phase right { purpose "r"; actors [actor]; focus [actor]; terminal failure; }
    transition to_left: begin -> left { when (count(enemy) > 0); priority 10; }
    transition to_right: begin -> right { when true; priority 20; }
  }
  binding sc2 {
    enemy = unit_group(owner=2, unit_type="Zealot", count=3, spawn=point_id(1532430748));
    actor = unit_group(owner=1, unit_type="Zealot", count=1, spawn=point_id(1963276538));
  }
}"""


def test_r03_dynamic_condition_beats_a_lower_priority_when_true_fallback():
    """R03: a `when true` fallback (priority 20) must not pre-empt a
    same-source, higher-priority (10) dynamic condition that is ALSO true."""
    h = Harness(MIXED_PRIORITY)
    assert h.kind("to_right") == "polled"          # demoted to the poll's fallback
    assert h.marked == {"begin"}                   # nothing fires before the first tick
    assert h.tick(to_left=True) == {"left"}


def test_r03_fallback_fires_when_the_dynamic_condition_is_false():
    assert Harness(MIXED_PRIORITY).tick(to_left=False) == {"right"}


def test_r03_swapping_priority_between_two_dynamic_siblings_changes_the_generated_code():
    """R03: two eventless DYNAMIC (non-trivial-guard) siblings from the same
    source used to produce byte-identical output regardless of which had
    the lower priority number -- priority played no role at all for that
    combination. After the fix they must be combined into one
    priority-ordered dispatcher, so swapping priorities changes which
    condition is checked (and therefore can win) first."""
    strat = """strategy dyn_prio_test {
      world {
        force enemy { side = "enemy"; role = "test"; }
        force actor { side = "ally"; role = "test"; }
      }
      initial { alive(enemy); alive(actor); }
      intent { pattern Test; primary alive(actor); success alive(actor); failure not (alive(actor)); }
      plan {
        start [begin];
        phase begin { purpose "b"; actors [actor]; focus [actor]; }
        phase left { purpose "l"; actors [actor]; focus [actor]; terminal success; }
        phase right { purpose "r"; actors [actor]; focus [actor]; terminal failure; }
        transition to_left: begin -> left { when alive(enemy); priority 20; }
        transition to_right: begin -> right { when (count(enemy) > 0); priority 10; }
      }
      binding sc2 {
        enemy = unit_group(owner=2, unit_type="Zealot", count=3, spawn=point_id(1532430748));
        actor = unit_group(owner=1, unit_type="Zealot", count=1, spawn=point_id(1963276538));
      }
    }"""
    swapped = strat.replace("priority 20", "TMP").replace("priority 10", "priority 20").replace("TMP", "priority 10")
    g1, _ = lower_to_galaxy(parse_source(strat))
    g2, _ = lower_to_galaxy(parse_source(swapped))
    assert g1 != g2, "swapping priority between two dynamic siblings had no effect on the generated code"


COUNTER_EQUIV_TEMPLATE = """strategy counter_equiv_test {{
  world {{
    force enemy {{ side = "enemy"; role = "test"; }}
    asset watcher {{ side = "ally"; role = "test"; }}
    region zone {{ role = "test"; }}
  }}
  initial {{ alive(enemy); alive(watcher); }}
  intent {{ pattern Test; primary alive(watcher); success alive(watcher); failure not (alive(watcher)); }}
  plan {{
    start [wait];
    phase wait {{ purpose "wait"; actors [enemy]; focus [watcher]; }}
    phase done {{ purpose "done"; actors [enemy]; focus [watcher]; terminal success; }}
    transition finish: wait -> done {{ on unit_died(enemy); when ({guard}); priority 10; }}
  }}
  binding sc2 {{
    enemy = unit_group(owner=2, unit_type="Zealot", count=1, spawn=point_id(1532430748));
    watcher = unit(owner=1, unit_type="Nexus", at=point_id(1963276538));
    zone = circle(center=point_id(1963276538), radius=8);
  }}
}}"""


def _eval_finish_guard_death_outside_zone(galaxy: str) -> bool:
    from galaxy_mini_interp import eval_expr
    guard_text = dispatch_guard(galaxy, "finish")
    guard_text = (
        guard_text
        .replace("DistanceBetweenPoints(UnitGetPosition(EventUnit()), PointFromId(1963276538)) <= 8.0", "false")
        .replace("UnitGroupHasUnit(gv_enemy, EventUnit()) == true", "true")
        .replace("gv_phase_active_wait == true", "true")
    )
    state = GalaxyMiniState()
    state.globals["gv_killed_in_5_enemy_4_zone"] = 0
    return bool(eval_expr(guard_text, state))


def test_r04_killed_in_bare_comparison_death_outside_zone_is_false():
    galaxy, _ = lower_to_galaxy(parse_source(COUNTER_EQUIV_TEMPLATE.format(guard="killed_in(enemy, zone) >= 1")))
    assert _eval_finish_guard_death_outside_zone(galaxy) is False


def test_r04_killed_in_plus_zero_death_outside_zone_is_still_false():
    """R04: killed_in(...) + 0 >= 1 must give the SAME answer as the bare
    comparison -- previously the `+ 0` pushed it through a fallback path
    that counted the death unconditionally, regardless of region."""
    galaxy, _ = lower_to_galaxy(parse_source(COUNTER_EQUIV_TEMPLATE.format(guard="killed_in(enemy, zone) + 0 >= 1")))
    assert _eval_finish_guard_death_outside_zone(galaxy) is False


def test_r04_killed_in_compared_to_itself_is_always_true():
    """R04: killed_in(f, r) == killed_in(f, r) is trivially reflexive and
    must always be true, regardless of the region check -- previously the
    right-hand occurrence fell back to an unconditional +1 while the
    left-hand one got the region-gated treatment, so they could disagree."""
    galaxy, _ = lower_to_galaxy(
        parse_source(COUNTER_EQUIV_TEMPLATE.format(guard="killed_in(enemy, zone) == killed_in(enemy, zone)"))
    )
    assert _eval_finish_guard_death_outside_zone(galaxy) is True
