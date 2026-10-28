"""
Regression tests for the control-flow findings in the v13 external audit
report (F02, F03, F04, F05, F13). Each test reproduces the reviewer's exact
minimal repro shape and asserts the FIXED behavior, not just "it compiles" --
the whole point of the audit was that broken control flow still produced
XML that passed the compiler's static checks.
"""


from stratagemdsl.frontend.antlr_parser import parse_source


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


def test_f10_subtraction_without_spaces_is_not_swallowed_into_a_negative_number():
    """F10: NUMBER used to include an optional leading '-' in the LEXER
    itself, so `3-1` (no space) tokenized as NUMBER("3") NUMBER("-1") --
    two adjacent numbers with no operator, not a subtraction."""
    from stratagemdsl.core.model import BinaryExpr, NumberExpr
    strat = """strategy f10_sub_test {
      world { force f { side = "ally"; role = "x"; } }
      initial { alive(f); }
      intent { pattern P; primary alive(f); success (3-1 == 2); failure not (alive(f)); }
      plan { start [b]; phase b { purpose "x"; actors [f]; focus [f]; terminal success; } }
      binding sc2 { f = unit_group(owner=1, unit_type="Zealot", count=3, spawn=point_id(1532430748)); }
    }"""
    s = parse_source(strat)
    success = s.intent.success
    assert isinstance(success, BinaryExpr) and success.op == "=="
    assert isinstance(success.left, BinaryExpr) and success.left.op == "-"
    assert success.left.left == NumberExpr(3.0)
    assert success.left.right == NumberExpr(1.0)


def test_f10_negative_coordinates_still_work_in_bindings():
    """point_xy(x, y) needs real signed world coordinates; propertyValue/
    bindingExpr get an explicit optional MINUS instead of relying on the
    lexer to glue the sign onto the number."""
    strat = """strategy f10_neg_test {
      world { force f { side = "ally"; role = "x"; } }
      initial { alive(f); }
      intent { pattern P; primary alive(f); success alive(f); failure not (alive(f)); }
      plan { start [b]; phase b { purpose "x"; actors [f]; focus [f]; terminal success; } }
      binding sc2 { f = unit_group(owner=1, unit_type="Zealot", count=3, spawn=point_xy(-50.5, 30)); }
    }"""
    s = parse_source(strat)
    spawn_call = s.bindings[0].value.args[-1].value
    assert spawn_call.args[0].value == -50.5


def test_f11_antlr_and_lark_agree_on_implies_associativity():
    """F11: `false implies true implies false` must parse to the SAME AST
    shape under both frontends. implies is right-associative in both now."""
    from stratagemdsl.frontend.lark_parser import parse_source as bootstrap_parse_source
    strat = """strategy f11_test {
      world { force f { side = "ally"; role = "x"; } }
      initial { alive(f); }
      intent { pattern P; primary alive(f); success (false implies true implies false); failure not (alive(f)); }
      plan { start [b]; phase b { purpose "x"; actors [f]; focus [f]; terminal success; } }
      binding sc2 { f = unit_group(owner=1, unit_type="Zealot", count=3, spawn=point_id(1532430748)); }
    }"""
    s_antlr = parse_source(strat)
    s_lark = bootstrap_parse_source(strat)
    assert s_antlr.intent.success == s_lark.intent.success
    # right-associative: false implies (true implies false)
    assert s_antlr.intent.success.right.op == "implies"
