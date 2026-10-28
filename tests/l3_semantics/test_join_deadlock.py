"""
Regression tests for P023_JOIN_DEADLOCK: a static reachability check that
catches an `all`/`atleast(k)` join whose required inputs are structurally
split across mutually-exclusive sibling branches (transitions competing on
priority from the same source, or on the same event) -- a real logic bug a
generated .strat can have even though it is perfectly valid syntax and
type-checks fine otherwise. Found via an external review of one specific
LLM-generated variant (adcc_reinforced), where two branches meant to be
independent were instead modeled as a priority-arbitrated fork feeding an
"all" join that could then never complete.
"""


from stratagemdsl.frontend.antlr_parser import parse_source
from stratagemdsl.semantics.validator import Validator


def _errors(strat_text: str) -> list[str]:
    s = parse_source(strat_text)
    return [str(x) for x in Validator(s).validate().items if "ERROR" in str(x).upper()]


DEADLOCKED_ALL_JOIN = """strategy deadlock_test {
  world {
    force vanguard { side = "ally"; role = "test"; }
    force reserve { side = "ally"; role = "test"; }
    force enemy { side = "enemy"; role = "test"; }
    asset watcher { side = "ally"; role = "test"; }
  }
  initial { alive(vanguard); alive(reserve); alive(enemy); alive(watcher); }
  intent { pattern Test; primary alive(watcher); success alive(watcher); failure not (alive(watcher)); }
  plan {
    start [begin];
    phase begin { purpose "b"; actors [vanguard]; focus [watcher]; }
    phase branch_a { purpose "a"; actors [vanguard]; focus [watcher]; }
    phase branch_b { purpose "b2"; actors [reserve]; focus [watcher]; }
    join ready all;
    phase done { purpose "d"; actors [vanguard]; focus [watcher]; terminal success; }
    transition to_a: begin -> branch_a { when alive(vanguard); priority 10; }
    transition to_b: begin -> branch_b { when alive(reserve); priority 11; }
    transition a_ready: branch_a -> ready { when true; priority 10; }
    transition b_ready: branch_b -> ready { when true; priority 10; }
    transition tail: ready -> done { when true; priority 10; }
  }
  binding sc2 {
    vanguard = unit_group(owner=1, unit_type="Zealot", count=3, spawn=point_id(1532430748));
    reserve = unit_group(owner=1, unit_type="Zealot", count=3, spawn=point_id(1532430764));
    enemy = unit_group(owner=2, unit_type="Zealot", count=3, spawn=point_id(9034952));
    watcher = unit(owner=1, unit_type="Nexus", at=point_id(1963276538));
  }
}"""


def test_all_join_fed_by_mutually_exclusive_siblings_is_rejected():
    errors = _errors(DEADLOCKED_ALL_JOIN)
    assert any("P023_JOIN_DEADLOCK" in e for e in errors), errors


DEADLOCKED_EVENT_SIBLINGS = """strategy deadlock_event_test {
  world {
    force vanguard { side = "ally"; role = "test"; }
    force reserve { side = "ally"; role = "test"; }
    force enemy { side = "enemy"; role = "test"; }
    asset watcher { side = "ally"; role = "test"; }
    region zone { role = "test"; }
  }
  initial { alive(vanguard); alive(reserve); alive(enemy); alive(watcher); }
  intent { pattern Test; primary alive(watcher); success alive(watcher); failure not (alive(watcher)); }
  plan {
    start [begin];
    phase begin { purpose "b"; actors [vanguard]; focus [watcher]; }
    phase branch_a { purpose "a"; actors [vanguard]; focus [watcher]; }
    phase branch_b { purpose "b2"; actors [reserve]; focus [watcher]; }
    join ready all;
    phase done { purpose "d"; actors [vanguard]; focus [watcher]; terminal success; }
    transition to_a: begin -> branch_a { on enter(enemy, zone); priority 10; }
    transition to_b: begin -> branch_b { on enter(enemy, zone); priority 11; }
    transition a_ready: branch_a -> ready { when true; priority 10; }
    transition b_ready: branch_b -> ready { when true; priority 10; }
    transition tail: ready -> done { when true; priority 10; }
  }
  binding sc2 {
    vanguard = unit_group(owner=1, unit_type="Zealot", count=3, spawn=point_id(1532430748));
    reserve = unit_group(owner=1, unit_type="Zealot", count=3, spawn=point_id(1532430764));
    enemy = unit_group(owner=2, unit_type="Zealot", count=3, spawn=point_id(9034952));
    watcher = unit(owner=1, unit_type="Nexus", at=point_id(1963276538));
    zone = circle(center=point_id(9034952), radius=6);
  }
}"""


def test_all_join_fed_by_same_event_siblings_is_rejected():
    """Same deadlock pattern, but the mutually-exclusive fork is two
    transitions competing on the exact same `on enter(...)` event (S03's
    combined-dispatcher case) rather than two eventless transitions."""
    errors = _errors(DEADLOCKED_EVENT_SIBLINGS)
    assert any("P023_JOIN_DEADLOCK" in e for e in errors), errors


LEGITIMATE_ALL_JOIN = """strategy legit_join_test {
  world {
    force left_f { side = "ally"; role = "test"; }
    force right_f { side = "ally"; role = "test"; }
    force enemy { side = "enemy"; role = "test"; }
  }
  initial { alive(left_f); alive(right_f); alive(enemy); }
  intent { pattern Test; primary alive(left_f); success alive(left_f); failure not (alive(left_f)); }
  plan {
    start [left, right];
    phase left { purpose "l"; actors [left_f]; focus [enemy]; }
    phase right { purpose "r"; actors [right_f]; focus [enemy]; }
    join ready all;
    phase done { purpose "d"; actors [left_f]; focus [enemy]; terminal success; }
    transition l_ready: left -> ready { when true; priority 10; }
    transition r_ready: right -> ready { when true; priority 10; }
    transition tail: ready -> done { when true; priority 10; }
  }
  binding sc2 {
    left_f = unit_group(owner=1, unit_type="Zealot", count=3, spawn=point_id(1532430748));
    right_f = unit_group(owner=1, unit_type="Zealot", count=3, spawn=point_id(1532430764));
    enemy = unit_group(owner=2, unit_type="Zealot", count=3, spawn=point_id(9034952));
  }
}"""


def test_all_join_from_genuinely_independent_start_phases_is_not_flagged():
    """Both of `ready`'s inputs come from DIFFERENT literal start phases --
    nothing forces a choice between them, so this must NOT be flagged."""
    errors = _errors(LEGITIMATE_ALL_JOIN)
    assert not any("P023_JOIN_DEADLOCK" in e for e in errors), errors


def test_any_join_with_exclusive_siblings_is_not_flagged():
    """An `any` join only needs ONE arrival, so competing siblings feeding
    it are fine -- whichever one wins the fork still satisfies `any`."""
    any_variant = DEADLOCKED_ALL_JOIN.replace("join ready all;", "join ready any;")
    errors = _errors(any_variant)
    assert not any("P023_JOIN_DEADLOCK" in e for e in errors), errors


FP_UNRELATED_FORK = """strategy fp_unrelated_fork_test {
  world {
    force left_f { side = "ally"; role = "test"; }
    force right_f { side = "ally"; role = "test"; }
    force enemy { side = "enemy"; role = "test"; }
  }
  initial { alive(left_f); alive(right_f); alive(enemy); }
  intent { pattern Test; primary alive(left_f); success alive(left_f); failure not (alive(left_f)); }
  plan {
    start [left, right, choice];
    phase left { purpose "l"; actors [left_f]; focus [enemy]; }
    phase right { purpose "r"; actors [right_f]; focus [enemy]; }
    join ready all;
    phase done { purpose "d"; actors [left_f]; focus [enemy]; terminal success; }
    phase choice { purpose "c"; actors [left_f]; focus [enemy]; }
    phase x { purpose "x"; actors [left_f]; focus [enemy]; terminal success; }
    phase y { purpose "y"; actors [left_f]; focus [enemy]; terminal failure; }
    transition l_ready: left -> ready { when true; priority 10; }
    transition r_ready: right -> ready { when true; priority 10; }
    transition tail: ready -> done { when true; priority 10; }
    transition to_x: choice -> x { when alive(left_f); priority 10; }
    transition to_y: choice -> y { when alive(right_f); priority 11; }
  }
  binding sc2 {
    left_f = unit_group(owner=1, unit_type="Zealot", count=3, spawn=point_id(1532430748));
    right_f = unit_group(owner=1, unit_type="Zealot", count=3, spawn=point_id(1532430764));
    enemy = unit_group(owner=2, unit_type="Zealot", count=3, spawn=point_id(9034952));
  }
}"""


def test_fp_unrelated_fork_elsewhere_in_plan_is_not_flagged():
    """A totally unrelated exclusive fork (choice -> x/y) that has nothing
    to do with reaching the join's inputs must not cause a false positive
    just because ITS OWN siblings, in isolation, can't reach the join."""
    assert not any("P023_JOIN_DEADLOCK" in e for e in _errors(FP_UNRELATED_FORK))


FP_DOWNSTREAM_FORK = """strategy fp_downstream_fork_test {
  world {
    force left_f { side = "ally"; role = "test"; }
    force right_f { side = "ally"; role = "test"; }
    force enemy { side = "enemy"; role = "test"; }
  }
  initial { alive(left_f); alive(right_f); alive(enemy); }
  intent { pattern Test; primary alive(left_f); success alive(left_f); failure not (alive(left_f)); }
  plan {
    start [left, right];
    phase left { purpose "l"; actors [left_f]; focus [enemy]; }
    phase right { purpose "r"; actors [right_f]; focus [enemy]; }
    join ready all;
    phase done { purpose "d"; actors [left_f]; focus [enemy]; }
    phase x { purpose "x"; actors [left_f]; focus [enemy]; terminal success; }
    phase y { purpose "y"; actors [left_f]; focus [enemy]; terminal failure; }
    transition l_ready: left -> ready { when true; priority 10; }
    transition r_ready: right -> ready { when true; priority 10; }
    transition tail: ready -> done { when true; priority 10; }
    transition to_x: done -> x { when alive(left_f); priority 10; }
    transition to_y: done -> y { when alive(right_f); priority 11; }
  }
  binding sc2 {
    left_f = unit_group(owner=1, unit_type="Zealot", count=3, spawn=point_id(1532430748));
    right_f = unit_group(owner=1, unit_type="Zealot", count=3, spawn=point_id(1532430764));
    enemy = unit_group(owner=2, unit_type="Zealot", count=3, spawn=point_id(9034952));
  }
}"""


def test_fp_fork_downstream_of_the_join_is_not_flagged():
    """An exclusive fork AFTER the join (done -> x/y) has no bearing on
    whether the join itself can be reached."""
    assert not any("P023_JOIN_DEADLOCK" in e for e in _errors(FP_DOWNSTREAM_FORK))


FP_INDEPENDENT_BRANCH_STARTS = """strategy fp_independent_branch_starts_test {
  world {
    force left_f { side = "ally"; role = "test"; }
    force right_f { side = "ally"; role = "test"; }
    force enemy { side = "enemy"; role = "test"; }
  }
  initial { alive(left_f); alive(right_f); alive(enemy); }
  intent { pattern Test; primary alive(left_f); success alive(left_f); failure not (alive(left_f)); }
  plan {
    start [choice, left, right];
    phase choice { purpose "c"; actors [left_f]; focus [enemy]; }
    phase left { purpose "l"; actors [left_f]; focus [enemy]; }
    phase right { purpose "r"; actors [right_f]; focus [enemy]; }
    join ready all;
    phase done { purpose "d"; actors [left_f]; focus [enemy]; terminal success; }
    transition choice_to_left: choice -> left { when alive(left_f); priority 10; }
    transition choice_to_right: choice -> right { when alive(right_f); priority 11; }
    transition l_ready: left -> ready { when true; priority 10; }
    transition r_ready: right -> ready { when true; priority 10; }
    transition tail: ready -> done { when true; priority 10; }
  }
  binding sc2 {
    left_f = unit_group(owner=1, unit_type="Zealot", count=3, spawn=point_id(1532430748));
    right_f = unit_group(owner=1, unit_type="Zealot", count=3, spawn=point_id(1532430764));
    enemy = unit_group(owner=2, unit_type="Zealot", count=3, spawn=point_id(9034952));
  }
}"""


def test_fp_branch_targets_that_are_also_their_own_independent_starts_is_not_flagged():
    """`left`/`right` are the targets of an exclusive fork AND independent
    `plan.start` entries in their own right -- reachable regardless of
    which way the fork resolves."""
    assert not any("P023_JOIN_DEADLOCK" in e for e in _errors(FP_INDEPENDENT_BRANCH_STARTS))


FP_ATLEAST_EXTERNAL_ARRIVAL = """strategy fp_atleast_external_test {
  world {
    force left_f { side = "ally"; role = "test"; }
    force right_f { side = "ally"; role = "test"; }
    force extra_f { side = "ally"; role = "test"; }
    force enemy { side = "enemy"; role = "test"; }
  }
  initial { alive(left_f); alive(right_f); alive(extra_f); alive(enemy); }
  intent { pattern Test; primary alive(left_f); success alive(left_f); failure not (alive(left_f)); }
  plan {
    start [choice, extra];
    phase choice { purpose "c"; actors [left_f]; focus [enemy]; }
    phase left { purpose "l"; actors [left_f]; focus [enemy]; }
    phase right { purpose "r"; actors [right_f]; focus [enemy]; }
    phase extra { purpose "e"; actors [extra_f]; focus [enemy]; }
    join ready atleast(2);
    phase done { purpose "d"; actors [left_f]; focus [enemy]; terminal success; }
    transition choice_to_left: choice -> left { when alive(left_f); priority 10; }
    transition choice_to_right: choice -> right { when alive(right_f); priority 11; }
    transition l_ready: left -> ready { when true; priority 10; }
    transition r_ready: right -> ready { when true; priority 10; }
    transition e_ready: extra -> ready { when true; priority 10; }
    transition tail: ready -> done { when true; priority 10; }
  }
  binding sc2 {
    left_f = unit_group(owner=1, unit_type="Zealot", count=3, spawn=point_id(1532430748));
    right_f = unit_group(owner=1, unit_type="Zealot", count=3, spawn=point_id(1532430764));
    extra_f = unit_group(owner=1, unit_type="Zealot", count=3, spawn=point_id(1532430780));
    enemy = unit_group(owner=2, unit_type="Zealot", count=3, spawn=point_id(9034952));
  }
}"""


def test_fp_atleast_with_an_independent_extra_arrival_is_not_flagged():
    """`ready` is atleast(2): whichever of left/right the fork picks
    contributes 1, and the independent `extra` start always contributes
    another 1, so the threshold is reachable under EVERY choice."""
    assert not any("P023_JOIN_DEADLOCK" in e for e in _errors(FP_ATLEAST_EXTERNAL_ARRIVAL))


FN_DIFFERENT_EVENTS = """strategy fn_different_events_test {
  world {
    force actor { side = "ally"; role = "test"; }
    force enemy { side = "enemy"; role = "test"; }
    region zone { role = "test"; }
  }
  initial { alive(actor); alive(enemy); }
  intent { pattern Test; primary alive(actor); success alive(actor); failure not (alive(actor)); }
  plan {
    start [choice];
    phase choice { purpose "c"; actors [actor]; focus [enemy]; }
    phase left { purpose "l"; actors [actor]; focus [enemy]; }
    phase right { purpose "r"; actors [actor]; focus [enemy]; }
    join ready all;
    phase done { purpose "d"; actors [actor]; focus [enemy]; terminal success; }
    transition choice_to_left: choice -> left { on enter(enemy, zone); priority 10; }
    transition choice_to_right: choice -> right { on unit_died(enemy); priority 11; }
    transition l_ready: left -> ready { when true; priority 10; }
    transition r_ready: right -> ready { when true; priority 10; }
    transition tail: ready -> done { when true; priority 10; }
  }
  binding sc2 {
    actor = unit_group(owner=1, unit_type="Zealot", count=3, spawn=point_id(1532430748));
    enemy = unit_group(owner=2, unit_type="Zealot", count=1, spawn=point_id(9034952));
    zone = circle(center=point_id(9034952), radius=6);
  }
}"""


def test_fn_exclusive_siblings_on_different_events_are_still_caught():
    """`choice` has two outgoing edges on DIFFERENT events (enter vs
    unit_died) -- still mutually exclusive (firing either one deactivates
    `choice`), even though they don't share an event signature and so
    were NOT grouped together by the compiler's own same-event dispatcher-
    combining logic. This must still be caught."""
    errors = _errors(FN_DIFFERENT_EVENTS)
    assert any("P023_JOIN_DEADLOCK" in e for e in errors), errors


DIRECT_DIFFERENT_EVENTS_ALL = """strategy direct_different_events_all_test {
  world {
    force actor { side = "ally"; role = "test"; }
    force enemy { side = "enemy"; role = "test"; }
    region zone { role = "test"; }
  }
  initial { alive(actor); alive(enemy); }
  intent { pattern Test; primary alive(actor); success alive(actor); failure not (alive(actor)); }
  plan {
    start [s];
    phase s { purpose "s"; actors [actor]; focus [enemy]; }
    join j all;
    phase done { purpose "d"; actors [actor]; focus [enemy]; terminal success; }
    transition a: s -> j { on enter(enemy, zone); priority 10; }
    transition b: s -> j { on unit_died(enemy); priority 11; }
    transition tail: j -> done { when true; priority 10; }
  }
  binding sc2 {
    actor = unit_group(owner=1, unit_type="Zealot", count=3, spawn=point_id(1532430748));
    enemy = unit_group(owner=2, unit_type="Zealot", count=1, spawn=point_id(9034952));
    zone = circle(center=point_id(9034952), radius=6);
  }
}"""


def test_x01_direct_exclusive_edges_into_join_are_caught_even_though_shared_source_is_a_start_phase():
    """X01: `a`/`b` compete directly from `s` (a start phase) straight into
    an all-join `j`. Both transitions' `.source` is `s`, which is always
    trivially reachable (it's a start phase) -- reachability of the SOURCE
    is not enough; the specific edge itself must not be one of the
    disabled (losing) siblings in whatever combination is being checked."""
    errors = _errors(DIRECT_DIFFERENT_EVENTS_ALL)
    assert any("P023_JOIN_DEADLOCK" in e for e in errors), errors


COMBINED_FORKS_LIMIT = """strategy combined_forks_limit_test {
  world {
    force p_f { side = "ally"; role = "test"; }
    force q_f { side = "ally"; role = "test"; }
    force enemy { side = "enemy"; role = "test"; }
  }
  initial { alive(p_f); alive(q_f); alive(enemy); }
  intent { pattern Test; primary alive(p_f); success alive(p_f); failure not (alive(p_f)); }
  plan {
    start [p, q];
    phase p { purpose "p"; actors [p_f]; focus [enemy]; }
    phase q { purpose "q"; actors [q_f]; focus [enemy]; }
    phase a { purpose "a"; actors [p_f]; focus [enemy]; }
    phase b { purpose "b"; actors [p_f]; focus [enemy]; }
    phase c { purpose "c"; actors [p_f]; focus [enemy]; }
    join j all;
    phase done { purpose "d"; actors [p_f]; focus [enemy]; terminal success; }
    transition p_to_a: p -> a { when alive(p_f); priority 10; }
    transition p_to_b: p -> b { when alive(q_f); priority 11; }
    transition p_to_c: p -> c { when true; priority 12; }
    transition q_to_a: q -> a { when alive(p_f); priority 10; }
    transition q_to_b: q -> b { when alive(q_f); priority 11; }
    transition q_to_c: q -> c { when true; priority 12; }
    transition a_j: a -> j { when true; priority 10; }
    transition b_j: b -> j { when true; priority 10; }
    transition c_j: c -> j { when true; priority 10; }
    transition tail: j -> done { when true; priority 10; }
  }
  binding sc2 {
    p_f = unit_group(owner=1, unit_type="Zealot", count=3, spawn=point_id(1532430748));
    q_f = unit_group(owner=1, unit_type="Zealot", count=3, spawn=point_id(1532430764));
    enemy = unit_group(owner=2, unit_type="Zealot", count=3, spawn=point_id(9034952));
  }
}"""


def test_two_independent_three_way_forks_that_jointly_cannot_cover_all_three_join_inputs():
    """`p` and `q` each independently pick ONE of {a, b, c}; `j` (all)
    needs all THREE distinct targets active, but at most 2 of {a,b,c} can
    ever be simultaneously chosen across p and q's independent picks. No
    SINGLE fork alone proves this (each fork's own choices individually
    still "reach" some subset of a/b/c depending on what the OTHER fork
    does), so this requires checking joint combinations across both
    forks together, not each one in isolation."""
    errors = _errors(COMBINED_FORKS_LIMIT)
    assert any("P023_JOIN_DEADLOCK" in e for e in errors), errors


def _core_plus_unrelated_forks(n_unrelated: int) -> str:
    """Same two-independent-3-way-forks-cannot-cover-3-targets deadlock
    core as `test_two_independent_three_way_forks_...` above (9 relevant
    combinations), padded with `n_unrelated` completely disconnected
    2-way forks that have no edge anywhere near the deadlocked join."""
    world = [
        'force p_f { side = "ally"; role = "test"; }',
        'force q_f { side = "ally"; role = "test"; }',
        'force enemy { side = "enemy"; role = "test"; }',
    ]
    initial = ["alive(p_f)", "alive(q_f)", "alive(enemy)"]
    nodes = [
        'phase p { purpose "p"; actors [p_f]; focus [enemy]; }',
        'phase q { purpose "q"; actors [q_f]; focus [enemy]; }',
        'phase a { purpose "a"; actors [p_f]; focus [enemy]; }',
        'phase b { purpose "b"; actors [p_f]; focus [enemy]; }',
        'phase c { purpose "c"; actors [p_f]; focus [enemy]; }',
        "join j all;",
        'phase done { purpose "d"; actors [p_f]; focus [enemy]; terminal success; }',
    ]
    transitions = [
        "transition p_to_a: p -> a { when alive(p_f); priority 10; }",
        "transition p_to_b: p -> b { when alive(q_f); priority 11; }",
        "transition p_to_c: p -> c { when true; priority 12; }",
        "transition q_to_a: q -> a { when alive(p_f); priority 10; }",
        "transition q_to_b: q -> b { when alive(q_f); priority 11; }",
        "transition q_to_c: q -> c { when true; priority 12; }",
        "transition a_j: a -> j { when true; priority 10; }",
        "transition b_j: b -> j { when true; priority 10; }",
        "transition c_j: c -> j { when true; priority 10; }",
        "transition tail: j -> done { when true; priority 10; }",
    ]
    starts = ["p", "q"]
    bindings = [
        'p_f = unit_group(owner=1, unit_type="Zealot", count=3, spawn=point_id(1532430748));',
        'q_f = unit_group(owner=1, unit_type="Zealot", count=3, spawn=point_id(1532430764));',
        'enemy = unit_group(owner=2, unit_type="Zealot", count=3, spawn=point_id(9034952));',
    ]
    for i in range(n_unrelated):
        world.append(f'force u{i}_f {{ side = "ally"; role = "test"; }}')
        initial.append(f"alive(u{i}_f)")
        nodes.append(f'phase unrelated_{i} {{ purpose "u"; actors [u{i}_f]; focus [enemy]; }}')
        nodes.append(f'phase x_{i} {{ purpose "x"; actors [u{i}_f]; focus [enemy]; terminal success; }}')
        nodes.append(f'phase y_{i} {{ purpose "y"; actors [u{i}_f]; focus [enemy]; terminal failure; }}')
        transitions.append(f"transition unrelated_{i}_to_x: unrelated_{i} -> x_{i} {{ when alive(u{i}_f); priority 10; }}")
        transitions.append(f"transition unrelated_{i}_to_y: unrelated_{i} -> y_{i} {{ when true; priority 11; }}")
        starts.append(f"unrelated_{i}")
        bindings.append(f'u{i}_f = unit_group(owner=1, unit_type="Zealot", count=1, spawn=point_id({1600000000 + i}));')

    nl = "\n    "
    return f"""strategy boundary_test {{
  world {{ {nl.join(world)} }}
  initial {{ {"; ".join(initial)}; }}
  intent {{ pattern Test; primary alive(p_f); success alive(p_f); failure not (alive(p_f)); }}
  plan {{
    start [{", ".join(starts)}];
    {nl.join(nodes)}
    {nl.join(transitions)}
  }}
  binding sc2 {{ {nl.join(bindings)} }}
}}"""


def test_unrelated_forks_elsewhere_do_not_hide_a_relevant_joint_deadlock():
    """The deadlocked core here only ever needs 9 relevant combinations to
    prove -- padding the plan with unrelated forks (which used to inflate
    the WHOLE-graph combination count past the 512 cap and force a
    fallback that missed this exact deadlock) must never change the
    result, since none of those unrelated forks can affect reachability
    to this join's inputs."""
    for n_unrelated in (0, 5, 6, 7):
        text = _core_plus_unrelated_forks(n_unrelated)
        errors = _errors(text)
        assert any("P023_JOIN_DEADLOCK" in e for e in errors), (n_unrelated, errors)
