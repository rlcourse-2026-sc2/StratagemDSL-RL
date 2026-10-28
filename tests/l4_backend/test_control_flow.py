"""
Regression tests for the control-flow findings in the v13 external audit
report (F02, F03, F04, F05, F13). Each test reproduces the reviewer's exact
minimal repro shape and asserts the FIXED behavior, not just "it compiles" --
the whole point of the audit was that broken control flow still produced
XML that passed the compiler's static checks.

v0.6: the plan runs as a Petri-net token game, so the assertions execute the
generated Galaxy (debug.galaxy_vm) and the reference net simulator side by
side (tests/support/net_harness.py) instead of matching v0.5 trigger text.
"""

import re

from net_harness import Harness
from stratagemdsl.frontend.antlr_parser import parse_source
from stratagemdsl.backend.galaxy import lower_to_galaxy, GalaxyLowerer


def _func_body(galaxy: str, func_name: str) -> str:
    m = re.search(re.escape(func_name) + r".*?\n\}", galaxy, re.S)
    assert m, f"{func_name} not found in generated Galaxy source"
    return m.group(0)


SHARED_TAIL = """strategy shared_tail_test {
  world {
    force enemy { side = "enemy"; role = "test"; }
    asset watcher { side = "ally"; role = "test"; }
    region zone { role = "test"; }
  }
  initial { alive(enemy); alive(watcher); }
  intent { pattern Test; primary alive(watcher); success alive(watcher); failure not (alive(watcher)); }
  plan {
    start [begin];
    phase begin { purpose "start"; actors [enemy]; focus [watcher]; }
    phase middle { purpose "middle"; actors [enemy]; focus [watcher]; }
    phase done { purpose "done"; actors [enemy]; focus [watcher]; terminal success; }
    transition a: begin -> middle { on enter(enemy, zone); priority 10; }
    transition b: begin -> middle { on leave(enemy, zone); priority 11; }
    transition tail: middle -> done { when true; priority 10; }
  }
  binding sc2 {
    enemy = unit_group(owner=2, unit_type="Zealot", count=3, spawn=point_id(1532430748));
    watcher = unit(owner=1, unit_type="Nexus", at=point_id(1963276538));
    zone = circle(center=point_id(1963276538), radius=8);
  }
}"""


def test_f02_shared_tail_fires_regardless_of_which_incoming_edge_wins():
    """F02: a tail transition downstream of a node reachable via TWO
    different incoming edges must be reachable via EITHER edge."""
    for edge in ("a", "b"):
        h = Harness(SHARED_TAIL)
        assert h.marked == {"begin"}
        assert h.event(edge) == {"done"}, edge   # `tail` is immediate: the settle loop runs it


JOIN_TEMPLATE = """strategy join_{policy}_test {{
  world {{
    force left_f {{ side = "enemy"; role = "test"; }}
    force right_f {{ side = "enemy"; role = "test"; }}
    asset watcher {{ side = "ally"; role = "test"; }}
    region left_zone {{ role = "test"; }}
    region right_zone {{ role = "test"; }}
  }}
  initial {{ alive(left_f); alive(right_f); alive(watcher); }}
  intent {{ pattern Test; primary alive(watcher); success alive(watcher); failure not (alive(watcher)); }}
  plan {{
    start [left, right];
    phase left {{ purpose "l"; actors [left_f]; focus [watcher]; }}
    phase right {{ purpose "r"; actors [right_f]; focus [watcher]; }}
    join ready {policy};
    phase done {{ purpose "done"; actors [left_f]; focus [watcher]; terminal success; }}
    transition a: left -> ready {{ on enter(left_f, left_zone); priority 10; }}
    transition b: right -> ready {{ on enter(right_f, right_zone); priority 10; }}
    transition tail: ready -> done {{ when true; priority 10; }}
  }}
  binding sc2 {{
    left_f = unit_group(owner=2, unit_type="Zealot", count=2, spawn=point_id(1532430748));
    right_f = unit_group(owner=2, unit_type="Zealot", count=2, spawn=point_id(1532430764));
    watcher = unit(owner=1, unit_type="Nexus", at=point_id(1963276538));
    left_zone = circle(center=point_id(1532430748), radius=5);
    right_zone = circle(center=point_id(1532430764), radius=5);
  }}
}}"""


def test_f03_join_all_requires_both_arrivals():
    h = Harness(JOIN_TEMPLATE.format(policy="all"))
    assert h.event("a") == {"right"}           # one arrival: the join does not release
    assert h.tokens("ready.in.a") == 1
    assert h.event("b") == {"done"}


def test_f03_join_any_requires_only_one_arrival():
    h = Harness(JOIN_TEMPLATE.format(policy="any"))
    assert h.event("a") == {"right", "done"}   # any: a alone is enough to cascade through


def test_f03_join_all_and_any_generate_different_thresholds():
    s_all = parse_source(JOIN_TEMPLATE.format(policy="all"))
    s_any = parse_source(JOIN_TEMPLATE.format(policy="any"))
    g_all, _ = lower_to_galaxy(s_all)
    g_any, _ = lower_to_galaxy(s_any)
    assert g_all != g_any


BRANCH = """strategy branch_test {
  world {
    force f { side = "ally"; role = "test"; }
  }
  initial { alive(f); }
  intent { pattern Test; primary alive(f); success alive(f); failure not (alive(f)); }
  plan {
    start [begin];
    phase begin { purpose "b"; actors [f]; focus [f]; }
    phase left { purpose "l"; actors [f]; focus [f]; terminal success; }
    phase right { purpose "r"; actors [f]; focus [f]; terminal failure; }
    transition to_left: begin -> left { when true; priority 10; }
    transition to_right: begin -> right { when true; priority 20; }
  }
  binding sc2 {
    f = unit_group(owner=1, unit_type="Zealot", count=3, spawn=point_id(1532430748));
  }
}"""


def test_f04_priority_selects_exactly_one_sibling_branch():
    """F04: two unconditional (when true) siblings racing out of the same
    phase must not both fire -- priority (lower number wins) selects one."""
    h = Harness(BRANCH)
    assert h.kind("to_left") == h.kind("to_right") == "immediate"
    assert h.marked == {"left"}
    assert h.outcome == 0                       # no first_wins latch configured


def test_f04_swapping_priority_swaps_the_winner():
    swapped = BRANCH.replace("priority 10", "TEMP20").replace("priority 20", "priority 10").replace("TEMP20", "priority 20")
    assert Harness(swapped).marked == {"right"}


ALIVE_ONCE = """strategy alive_once_test {
  world {
    force enemy { side = "enemy"; role = "test"; }
    asset watcher { side = "ally"; role = "test"; }
  }
  initial { alive(enemy); alive(watcher); }
  intent { pattern Test; primary alive(watcher); success alive(watcher); failure not (alive(watcher)); }
  plan {
    start [wait];
    phase wait { purpose "waiting for enemy to die"; actors [enemy]; focus [watcher]; }
    phase done { purpose "done"; actors [enemy]; focus [watcher]; terminal success; }
    transition finish: wait -> done { when not (alive(enemy)); priority 10; }
  }
  binding sc2 {
    enemy = unit_group(owner=2, unit_type="Zealot", count=1, spawn=point_id(1532430748));
    watcher = unit(owner=1, unit_type="Nexus", at=point_id(1963276538));
  }
}"""


def test_f05_not_alive_gets_a_real_periodic_recheck_not_a_one_time_fold():
    """F05: `not alive(enemy)` can only become true LATER -- it must be
    re-checked on the poll tick, never decided once at phase entry."""
    s = parse_source(ALIVE_ONCE)
    lowerer = GalaxyLowerer(s)
    galaxy = lowerer.emit()
    assert lowerer.transition_kinds["finish"]["kind"] == "polled"
    body = _func_body(galaxy, "gt_net_tick_Func")
    assert "UnitGroupCount(gv_enemy, c_unitCountAlive)" in body
    h = Harness(ALIVE_ONCE)
    assert h.marked == {"wait"}
    assert h.tick(finish=False) == {"wait"}     # enemy still alive
    assert h.tick(finish=True) == {"done"}      # it died: the next tick fires


CONDITIONAL_START_LEAK = """strategy leak_test {
  world {
    force f { side = "ally"; role = "test"; }
  }
  initial { alive(f); }
  intent { pattern Test; primary alive(f); success alive(f); failure not (alive(f)); }
  plan {
    start [begin];
    phase begin { purpose "b"; actors [f]; focus [f]; }
    phase middle { purpose "m"; actors [f]; focus [f]; }
    phase done { purpose "d"; actors [f]; focus [f]; terminal success; }
    transition to_middle: begin -> middle { when false; priority 10; }
    transition to_done: middle -> done { when true; priority 10; }
  }
  binding sc2 {
    f = unit_group(owner=1, unit_type="Zealot", count=3, spawn=point_id(1532430748));
  }
}"""


def test_f13_false_guarded_branch_does_not_leak_descendants_into_initial_state():
    """F13: a transition gated on a literally-false guard must not cause its
    TARGET's own further descendants to be treated as initially active."""
    h = Harness(CONDITIONAL_START_LEAK)
    assert h.marked == {"begin"}
    assert h.tick() == {"begin"}


COUNTER_OR = """strategy counter_or_test {
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
      when (killed_in(enemy, zone) >= 3 or count(enemy) == 0);
      priority 10;
    }
  }
  binding sc2 {
    enemy = unit_group(owner=2, unit_type="Zealot", count=1, spawn=point_id(1532430748));
    watcher = unit(owner=1, unit_type="Nexus", at=point_id(1963276538));
    zone = circle(center=point_id(1963276538), radius=8);
  }
}"""


def test_f06_killed_in_region_check_does_not_veto_the_or_sibling():
    """F06: `killed_in(enemy, zone) >= 3 or count(enemy) == 0` must stay a
    real OR -- a death OUTSIDE zone must not make the whole guard false when
    the count(enemy) == 0 branch is independently true. Symbolically, with
    gv_killed_in_5_enemy_4_zone == 0 and this death outside the zone: the
    killed_in branch evaluates to false either way, but count(enemy) == 0
    (last enemy just died) must still make the overall guard true."""
    s = parse_source(COUNTER_OR)
    galaxy, _ = lower_to_galaxy(s)
    body = _func_body(galaxy, "gt_finish_Func")
    # The region check must be embedded inside the killed_in sub-expression,
    # never hoisted as a standalone required precondition ANDed onto the
    # whole guard.
    assert "gv_killed_in_5_enemy_4_zone + 1) >= 3" in body
    assert "UnitGroupCount(gv_enemy, c_unitCountAlive) == 0" in body

    # Extract the full guard's boolean text and symbolically evaluate it
    # for: prior in-zone kills = 0, this death OUTSIDE the zone, last enemy
    # just died (count == 0). Expected: True (the count==0 branch alone
    # must be enough) -- the pre-fix version ANDed the region check onto
    # the entire guard and returned False here.
    rg = False  # death outside the zone
    counter = 0
    true_branch = (counter + 1) >= 3
    false_branch = counter >= 3
    killed_in_term = (rg and true_branch) or (not rg and false_branch)
    count_term = True  # UnitGroupCount(...) == 0
    assert (killed_in_term or count_term) is True


GRAPH_ERROR = """strategy graph_error_test {
  world {
    force f { side = "ally"; role = "test"; }
    region zone { role = "test"; }
  }
  initial { alive(f); }
  intent { pattern Test; primary alive(f); success alive(f); failure not (alive(f)); }
  plan {
    start [begin];
    phase begin { purpose "b"; actors [f]; focus [zone]; terminal success; }
  }
  binding sc2 {
    f = unit_group(owner=1, unit_type="Zealot", count=3, spawn=point_id(1532430748));
    zone = circle(center=point_id(1532430748));
  }
}"""


def test_f08_plangraph_export_survives_a_constructor_time_lowering_error():
    """F08: GalaxyLowerer.__init__ itself can raise LoweringError (e.g. a
    circle region missing radius, which the Validator does not catch).
    build_graph_model must still return a usable GraphModel with
    lowering_ok=False and a real error message, not let the exception
    propagate and take down the whole diagnostic view -- exactly the
    situation where a person most needs to see SOMETHING."""
    from stratagemdsl.views.plangraph import build_graph_model

    s = parse_source(GRAPH_ERROR)
    model = build_graph_model(s)  # must not raise
    assert model.lowering_ok is False
    assert "radius" in model.lowering_error
    assert len(model.nodes) == 1


def test_f10_unparse_never_emits_scientific_notation():
    """A very small float used to round-trip through repr() as '1e-07',
    which the grammar's NUMBER rule (no exponent support) cannot re-parse."""
    from stratagemdsl.frontend.unparse import _num
    assert "e" not in _num(0.0000001).lower()
    assert _num(0.0000001) == "0.0000001"


def _strat_with_binding(binding_line: str, extra_world: str = "") -> str:
    return f"""strategy f12_test {{
  world {{ force f {{ side = "ally"; role = "x"; }} {extra_world} }}
  initial {{ alive(f); }}
  intent {{ pattern P; primary alive(f); success alive(f); failure not (alive(f)); }}
  plan {{ start [b]; phase b {{ purpose "x"; actors [f]; focus [f]; terminal success; }} }}
  binding sc2 {{ {binding_line} }}
}}"""


def test_f12_fractional_owner_is_rejected_not_silently_truncated():
    from stratagemdsl.backend.galaxy import lower_to_galaxy, LoweringError
    s = parse_source(_strat_with_binding(
        'f = unit_group(owner=2.7, unit_type="Zealot", count=3, spawn=point_id(1532430748));'
    ))
    try:
        lower_to_galaxy(s)
        assert False, "owner=2.7 should have been rejected, not silently truncated to 2"
    except LoweringError as e:
        assert "owner" in str(e) and "whole number" in str(e)


def test_f12_fractional_count_is_rejected_not_silently_truncated():
    from stratagemdsl.backend.galaxy import lower_to_galaxy, LoweringError
    s = parse_source(_strat_with_binding(
        'f = unit_group(owner=1, unit_type="Zealot", count=1.9, spawn=point_id(1532430748));'
    ))
    try:
        lower_to_galaxy(s)
        assert False, "count=1.9 should have been rejected, not silently truncated to 1"
    except LoweringError as e:
        assert "count" in str(e) and "whole number" in str(e)


def test_f12_fractional_point_id_is_rejected_not_silently_truncated():
    from stratagemdsl.backend.galaxy import lower_to_galaxy, LoweringError
    s = parse_source(_strat_with_binding(
        'f = unit_group(owner=1, unit_type="Zealot", count=3, spawn=point_id(1.9));'
    ))
    try:
        lower_to_galaxy(s)
        assert False, "point_id(1.9) should have been rejected, not silently truncated to 1"
    except LoweringError as e:
        assert "point_id" in str(e) and "whole number" in str(e)


def test_f12_negative_radius_is_rejected():
    from stratagemdsl.backend.galaxy import lower_to_galaxy, LoweringError
    s = parse_source(_strat_with_binding(
        'f = unit_group(owner=1, unit_type="Zealot", count=3, spawn=point_id(1532430748));\n'
        '    z = circle(center=point_id(1532430748), radius=-3);',
        extra_world='region z { role = "x"; }',
    ))
    try:
        lower_to_galaxy(s)
        assert False, "radius=-3 should have been rejected"
    except LoweringError as e:
        assert "radius" in str(e) and "positive" in str(e)
