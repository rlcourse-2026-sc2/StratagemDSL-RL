"""Unit tests for the ANTLR visitor in frontend/antlr_parser.py.

Each test parses one small strategy and checks the AST object built by the
visitor method named in the test. The visitor is nested inside parse_source,
so the tests go through that entry point.
python -m pytest -q tests/l1_frontend/test_antlr_parser_visitors.py

"""
from stratagemdsl.core.model import (
    ActionBlock, BinaryExpr, Binding, BindingArg, BindingCall, BoolExpr,
    CallExpr, DerivedFact, EntityDecl, Intent, Join, NameExpr, NumberExpr,
    Phase, StringExpr, Transition, UnaryExpr,
)
from stratagemdsl.frontend.antlr_parser import parse_source


def parse(world="force f { }", intent=None, plan=None, initial="", semantics="", binding=""):
    if intent is None:
        intent = "primary true; success true; failure false;"
    if plan is None:
        plan = 'start []; phase only { purpose "only"; }'
    source = (
        "strategy sample {\n"
        f"  world {{ {world} }}\n"
        f"  {initial}\n"
        f"  intent {{ {intent} }}\n"
        f"  {semantics}\n"
        f"  plan {{ {plan} }}\n"
        f"  {binding}\n"
        "}\n"
    )
    return parse_source(source)


def test_visit_document_and_strategy_decl_keep_the_name_and_section_order():
    strategy = parse(
        world='force allied { side = "ally"; } asset home { }',
        initial="initial { alive(allied); }",
        intent="primary alive(allied); success alive(allied); failure alive(home);",
    )
    assert strategy.name == "sample"
    assert [entity.name for entity in strategy.world] == ["allied", "home"]
    assert strategy.initial == [CallExpr("alive", [NameExpr("allied")])]


def test_visit_world_section_visits_each_entity_decl_in_source_order():
    strategy = parse(
        world=(
            'force allied_force { side = "ally"; role = "covert_strike"; }'
            'asset allied_home { }'
            "region enemy_rear_zone { }"
            "route supply { }"
        )
    )
    assert strategy.world == [
        EntityDecl("force", "allied_force", {"side": "ally", "role": "covert_strike"}),
        EntityDecl("asset", "allied_home", {}),
        EntityDecl("region", "enemy_rear_zone", {}),
        EntityDecl("route", "supply", {}),
    ]


def test_visit_property_value_keeps_strings_bools_glued_numbers_names_and_lists():
    strategy = parse(
        world=(
            "force f { "
            'side = "ally"; flag = true; off = false; count = -3; ratio = -1.5; '
            "role = phase; tags = [\"a\", 1, true]; "
            "}"
        )
    )
    assert strategy.world[0].properties == {
        "side": "ally",
        "flag": True,
        "off": False,
        "count": -3.0,
        "ratio": -1.5,
        "role": "phase",
        "tags": ["a", 1.0, True],
    }


def test_visit_expr_collapses_the_precedence_chain_around_or_and_not():
    strategy = parse(
        intent=(
            "primary (not (alive(allied_force)) or destroyed(allied_home)); "
            "success true; failure false;"
        )
    )
    assert strategy.intent.primary == BinaryExpr(
        "or",
        UnaryExpr("not", CallExpr("alive", [NameExpr("allied_force")])),
        CallExpr("destroyed", [NameExpr("allied_home")]),
    )


def test_visit_left_op_respects_product_over_sum_and_right_associative_implies():
    strategy = parse(
        intent=(
            "primary 1 + 2 * 3; "
            "secondary a implies b implies c; "
            "success a < b + c; "
            "failure -1;"
        )
    )
    two_times_three = BinaryExpr("*", NumberExpr(2.0), NumberExpr(3.0))
    assert strategy.intent.primary == BinaryExpr("+", NumberExpr(1.0), two_times_three)
    assert strategy.intent.secondary == BinaryExpr(
        "implies",
        NameExpr("a"),
        BinaryExpr("implies", NameExpr("b"), NameExpr("c")),
    )
    assert strategy.intent.success == BinaryExpr(
        "<",
        NameExpr("a"),
        BinaryExpr("+", NameExpr("b"), NameExpr("c")),
    )
    assert strategy.intent.failure == UnaryExpr("-", NumberExpr(1.0))


def test_visit_atom_and_literal_distinguish_calls_names_strings_and_bools():
    strategy = parse(
        intent=(
            'primary alive(); '
            'secondary "a\\n"; '
            "success true; "
            "failure watcher;"
        )
    )
    assert strategy.intent.primary == CallExpr("alive", [])
    assert strategy.intent.secondary == StringExpr("a\n")
    assert strategy.intent.success == BoolExpr(True)
    assert strategy.intent.failure == NameExpr("watcher")


def test_visit_intent_section_reads_pattern_bindings_and_optional_secondary():
    bare = parse(intent="pattern Test; primary true; success true; failure false;")
    assert bare.intent == Intent("Test", BoolExpr(True), None, BoolExpr(True), BoolExpr(False), {})

    bound = parse(
        intent=(
            "pattern CovertBypass { covert_force = allied_force; blocker = enemy_blockers; } "
            "primary alive(allied_force); secondary alive(blocker); "
            "success destroyed(enemy_home); failure alive(allied_home);"
        )
    )
    assert bound.intent.pattern == "CovertBypass"
    assert bound.intent.pattern_bindings == {
        "covert_force": "allied_force",
        "blocker": "enemy_blockers",
    }
    assert bound.intent.secondary == CallExpr("alive", [NameExpr("blocker")])


def test_visit_initial_and_derived_decl_collect_expression_lists():
    strategy = parse(
        initial="initial { alive(f); not (alive(home)); }",
        semantics="semantics { derive ready = alive(f); derive lost = destroyed(home); }",
    )
    assert strategy.initial == [
        CallExpr("alive", [NameExpr("f")]),
        UnaryExpr("not", CallExpr("alive", [NameExpr("home")])),
    ]
    assert strategy.derived == [
        DerivedFact("ready", CallExpr("alive", [NameExpr("f")])),
        DerivedFact("lost", CallExpr("destroyed", [NameExpr("home")])),
    ]


def test_visit_phase_decl_fills_optional_fields_and_action_block_mode():
    strategy = parse(
        world="force enemy { } asset watcher { } region zone { }",
        plan="""
        start [begin];
        phase begin {
          purpose "start";
          actors [enemy, watcher];
          focus [zone];
          entry alive(enemy);
          do parallel { move(enemy); hold(watcher); }
          invariant true;
          exit false;
          terminal success;
        }
        phase plain { purpose "plain"; do { move(enemy); } terminal failure; }
        """,
    )
    begin, plain = strategy.plan.nodes
    assert begin == Phase(
        id="begin",
        purpose="start",
        actors=["enemy", "watcher"],
        focus=["zone"],
        entry=CallExpr("alive", [NameExpr("enemy")]),
        actions=ActionBlock("parallel", [
            CallExpr("move", [NameExpr("enemy")]),
            CallExpr("hold", [NameExpr("watcher")]),
        ]),
        invariant=BoolExpr(True),
        exit=BoolExpr(False),
        terminal="success",
    )
    assert plain.actions == ActionBlock("sequence", [CallExpr("move", [NameExpr("enemy")])])
    assert plain.terminal == "failure"
    assert plain.actors == []
    assert strategy.plan.start == ["begin"]


def test_visit_join_decl_reads_all_any_and_atleast():
    strategy = parse(
        plan="""
        start [];
        phase only { purpose "only"; }
        join everyone all;
        join anyone any;
        join enough atleast(2);
        """
    )
    assert strategy.plan.nodes[1:] == [
        Join("everyone", "all", None),
        Join("anyone", "any", None),
        Join("enough", "atleast", 2),
    ]


def test_visit_transition_decl_uses_its_own_three_ids_not_ids_inside_the_body():
    strategy = parse(
        plan="""
        start [middle];
        phase middle { purpose "middle"; }
        phase done { purpose "done"; }
        transition tail: middle -> done {
          on enter(enemy, zone);
          when alive(watcher);
          do sequence { move(enemy); }
          priority 11;
        }
        """
    )
    assert strategy.plan.transitions == [
        Transition(
            id="tail",
            source="middle",
            target="done",
            event=CallExpr("enter", [NameExpr("enemy"), NameExpr("zone")]),
            guard=CallExpr("alive", [NameExpr("watcher")]),
            actions=ActionBlock("sequence", [CallExpr("move", [NameExpr("enemy")])]),
            priority=11,
        )
    ]


def test_visit_binding_expr_reads_calls_route_lists_and_scalars():
    strategy = parse(
        binding="""
        binding sc2 {
          enemy = unit(owner=2, unit_type="Zealot");
          path = route(1);
          nums = [-1.5, 2];
          flag = false;
          label = phase;
        }
        """
    )
    assert strategy.backend == "sc2"
    assert strategy.bindings == [
        Binding("enemy", BindingCall("unit", [
            BindingArg("owner", 2.0),
            BindingArg("unit_type", "Zealot"),
        ])),
        Binding("path", BindingCall("route", [BindingArg(None, 1.0)])),
        Binding("nums", [-1.5, 2.0]),
        Binding("flag", False),
        Binding("label", "phase"),
    ]
