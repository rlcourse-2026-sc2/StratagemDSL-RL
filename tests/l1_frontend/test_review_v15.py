"""
Regression tests for the v15-review findings (R01-R05), using
_galaxy_mini_interp to actually EXECUTE the generated Galaxy code's
assignments/if-chains against a simulated globals dict, rather than
asserting on substrings of the generated text. A prior review correctly
pointed out that text-substring assertions can't distinguish correct
nesting/ordering from incorrect nesting/ordering that happens to mention
the same variable names.
"""


from stratagemdsl.frontend.antlr_parser import parse_source


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


def test_r05_numeric_roundtrip_preserves_a_very_small_value():
    """R05: unparse's scientific-notation avoidance used to round to a fixed
    number of decimal places, silently turning 1e-11 into 0.0 -- a real
    value change, not just a formatting change."""
    from stratagemdsl.frontend.unparse import unparse

    strat = """strategy numeric_precision_test {
      world { force f { side = "ally"; role = "x"; } }
      initial { alive(f); }
      intent { pattern P; primary alive(f); success alive(f); failure not (alive(f)); }
      plan {
        start [b];
        phase b { purpose "x"; actors [f]; focus [f]; }
        phase c { purpose "y"; actors [f]; focus [f]; terminal success; }
        transition t: b -> c { when 0.00000000001 > 0; priority 10; }
      }
      binding sc2 { f = unit_group(owner=1, unit_type="Zealot", count=3, spawn=point_id(1532430748)); }
    }"""
    s = parse_source(strat)
    original_guard = s.plan.transitions[0].guard
    reparsed = parse_source(unparse(s))
    assert reparsed.plan.transitions[0].guard == original_guard
