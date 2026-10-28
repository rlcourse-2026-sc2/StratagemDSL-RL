"""Layer 0: the AST model and diagnostics need nothing else.

Generated cases are read from files, one at a time:

    python tests/l0_architecture/test_core.py tests/l0_architecture/cases
"""
import sys
from pathlib import Path

import pytest

from stratagemdsl.core.ast_utils import binding_arg, walk_calls, binding_named
from stratagemdsl.core.diagnostics import DiagnosticBag, Diagnostic
from stratagemdsl.core.model import Place, BinaryExpr, UnaryExpr,BindingArg, BindingCall, CallExpr, NameExpr, NumberExpr, Strategy, Phase, ActionBlock, Join, Transition, DerivedFact, Intent, EntityDecl, Plan, Binding, BindingCall, BindingArg, CallExpr, NameExpr, NumberExpr, StringExpr, BoolExpr


def test_walk_calls_visits_nested_calls_outermost_first():
    e = BinaryExpr(">=", CallExpr("count", [CallExpr("inner", [NameExpr("f")])]), NumberExpr(2))
    assert [c.name for c in walk_calls(e)] == ["count", "inner"]


def test_binding_arg_prefers_named_then_positional():
    call = BindingCall("circle", [BindingArg(None, 5), BindingArg("radius", 3)])
    assert binding_arg(call, "radius", 1) == 3
    assert binding_arg(call, "center", 0) == 5
    assert binding_arg(call, "missing", 7, "default") == "default"


def test_diagnostic_bag_separates_errors_and_warnings():
    bag = DiagnosticBag()
    bag.warn("W1", "only a warning")
    assert not bag.has_errors
    bag.error("E1", "broken")
    assert bag.has_errors and [str(d) for d in bag.items] == ["[WARNING] W1: only a warning", "[ERROR] E1: broken"]

def test_binding_named_returns_default_when_missing():
    call = BindingCall("circle", [BindingArg("radius", 3)])
    assert binding_named(call, "radius") == 3
    assert binding_named(call, "center", "none") == "none"

def _strategy() -> Strategy:
    count = CallExpr("count", [NameExpr("f")])
    phase = Phase(id="p", purpose="hold", actors=["ally"], actions=ActionBlock("sequence", [count]))
    join = Join(id="j", policy="all")
    return Strategy(
        name="s",
        world=[EntityDecl("unit", "ally", {"race": "zerg"})],
        initial=[BoolExpr(True)],
        intent=Intent(None, NameExpr("goal"), None, BoolExpr(True), BoolExpr(False)),
        derived=[DerivedFact("near", BinaryExpr("<", NumberExpr(1), NumberExpr(2)))],
        plan=Plan(
            start=["p"],
            nodes=[phase, join],
            transitions=[Transition("t", "p", "j", count, StringExpr("x"), None, 1)],
        ),
        backend=None,
        bindings=[Binding("area", BindingCall("circle", [BindingArg("radius", 3.0)]))],
    )

def test_strategy_to_dict_keeps_nested_fields():
    data = _strategy().to_dict()
    assert data["name"] == "s"
    assert data["world"][0]["properties"] == {"race": "zerg"}
    assert data["plan"]["nodes"][0]["actions"]["actions"][0]["name"] == "count"
    assert data["bindings"][0]["value"]["args"][0] == {"name": "radius", "value": 3.0}


def test_default_lists_are_not_shared():
    assert CallExpr("a").args is not CallExpr("b").args
    assert Phase("p", "hold").actors is not Phase("q", "hold").actors

def test_diagnostic_string_defaults_to_error():
    assert str(Diagnostic("E1", "broken")) == "[ERROR] E1: broken"

def test_extend_appends_without_marking_warnings_as_errors():
    bag = DiagnosticBag()
    bag.extend([Diagnostic("W1", "note", "warning")])
    assert bag.items[0].code == "W1"
    assert not bag.has_errors

def test_remaining_ast_util_branches():
    assert list(walk_calls(None)) == []
    assert [c.name for c in walk_calls(UnaryExpr("not", CallExpr("inner")))] == ["inner"]
    assert binding_arg(CallExpr("count"), "radius", 0, "default") == "default"


def test_join_plan_nests_comparison_guard_and_binding_call():
    """Shape of examples/learning/02_join_and_counter.strat."""
    losses = BinaryExpr(
        ">=",
        CallExpr("killed_in", [NameExpr("guards"), NameExpr("gate")]),
        NumberExpr(2.0),
    )
    release_when = BinaryExpr(
        "and",
        BinaryExpr(
            "and",
            CallExpr("in_region", [NameExpr("allies"), NameExpr("gate")]),
            NameExpr("losses_observed"),
        ),
        CallExpr("alive", [NameExpr("allies")]),
    )
    gate = BindingCall(
        "circle",
        [
            BindingArg("center", BindingCall("point_xy", [BindingArg(None, 54.99), BindingArg(None, 47.18)])),
            BindingArg("radius", 8.0),
        ],
    )
    plan = Plan(
        start=["approach_watch", "losses_watch", "fail_watch"],
        nodes=[
            Phase("approach_watch", "Observe arrival"),
            Phase("losses_watch", "Observe two losses in the zone"),
            Join("ready", "all"),
            Phase(
                "exploit",
                "Recheck both conditions after the join",
                actors=["allies"],
                actions=ActionBlock("sequence", [CallExpr("attack", [NameExpr("allies"), NameExpr("base")])]),
            ),
        ],
        transitions=[
            Transition(
                "arrival",
                "approach_watch",
                "ready",
                CallExpr("enter", [NameExpr("allies"), NameExpr("gate")]),
                CallExpr("alive", [NameExpr("allies")]),
                None,
                10,
            ),
            Transition("release", "ready", "exploit", None, release_when, None, 10),
        ],
    )

    ready = plan.nodes[2]
    assert isinstance(ready, Join) and ready.policy == "all" and ready.quorum is None
    assert plan.transitions[0].target == ready.id
    assert plan.transitions[1].event is None
    assert [c.name for c in walk_calls(losses)] == ["killed_in"]
    assert [c.name for c in walk_calls(release_when)] == ["in_region", "alive"]
    center = binding_named(gate, "center")
    assert binding_named(gate, "radius") == 8.0
    assert binding_arg(center, "x", 0) == 54.99
    assert binding_arg(center, "y", 1) == 47.18


def test_pattern_intent_nests_comparisons_on_a_transition():
    """Shape of examples/learning/03_typed_feint.strat."""
    exposed = BinaryExpr(
        "and",
        BinaryExpr("==", CallExpr("count", [NameExpr("defenders")]), NumberExpr(3.0)),
        BinaryExpr("<", CallExpr("count_in", [NameExpr("defenders"), NameExpr("real_zone")]), NumberExpr(2.0)),
    )
    induce = Transition(
        "induce",
        "feint",
        "observe",
        CallExpr("enter", [NameExpr("decoy"), NameExpr("trigger_zone")]),
        BinaryExpr(
            "and",
            CallExpr("alive", [NameExpr("main")]),
            BinaryExpr(">=", CallExpr("count_in", [NameExpr("defenders"), NameExpr("real_zone")]), NumberExpr(2.0)),
        ),
        ActionBlock("sequence", [CallExpr("retarget", [NameExpr("defenders"), NameExpr("fake")])]),
        10,
    )
    strategy = Strategy(
        name="TypedFeint",
        world=[EntityDecl("region", "trigger_zone")],
        initial=[],
        intent=Intent(
            "Feint",
            CallExpr("destroyed", [NameExpr("real")]),
            None,
            CallExpr("destroyed", [NameExpr("real")]),
            UnaryExpr("not", CallExpr("alive", [NameExpr("main")])),
            {
                "decoy": "decoy",
                "fake_target": "fake",
                "defenders": "defenders",
                "main_force": "main",
                "real_target": "real",
            },
        ),
        derived=[DerivedFact("exposed", exposed)],
        plan=Plan(start=["feint", "fail_watch"], nodes=[], transitions=[induce]),
        backend="sc2",
        bindings=[],
    )

    assert strategy.intent.pattern == "Feint"
    assert strategy.intent.pattern_bindings["real_target"] == "real"
    assert strategy.intent.secondary is None
    assert [c.name for c in walk_calls(strategy.derived[0].expr)] == ["count", "count_in"]
    assert [c.name for c in walk_calls(induce.guard)] == ["alive", "count_in"]
    assert induce.event.name == "enter"
    assert induce.actions.mode == "sequence" and induce.actions.actions[0].name == "retarget"
    assert strategy.to_dict()["intent"]["pattern_bindings"]["main_force"] == "main"

def test_join_and_counter():
    strategy = Strategy(
        name='JoinAndCounter',
        world=[
            EntityDecl(
                kind='force',
                name='allies',
                properties={'side': 'ally', 'role': 'main_attack'},
            ),
            EntityDecl(
                kind='force',
                name='guards',
                properties={'side': 'enemy', 'role': 'mobile_defense'},
            ),
            EntityDecl(kind='asset', name='base', properties={'side': 'enemy', 'role': 'critical'}),
            EntityDecl(kind='region', name='gate', properties={'role': 'observation_zone'}),        
        ],
        initial=[],
        intent=Intent(
            pattern=None,
            primary=CallExpr(name='destroyed', args=[NameExpr(name='base')]),
            secondary=None,
            success=CallExpr(name='destroyed', args=[NameExpr(name='base')]),
            failure=UnaryExpr(op='not', operand=CallExpr(name='alive', args=[NameExpr(name='allies')])),
        ),
        derived=[
            DerivedFact(
                name='losses_observed',
                expr=BinaryExpr(
                    op='>=',
                    left=CallExpr(name='killed_in', args=[NameExpr(name='guards'), NameExpr(name='gate')]),
                    right=NumberExpr(value=2.0),
                ),
            ),
        ],
        plan=Plan(
            start=['approach_watch', 'losses_watch', 'fail_watch'],
            nodes=[
                Phase(id='approach_watch', purpose='Observe arrival'),
                Phase(id='losses_watch', purpose='Observe two losses in the zone'),
                Join(id='ready', policy='all'),
                Phase(
                    id='exploit',
                    purpose='Recheck both conditions after the join',
                    actors=['allies'],
                    actions=ActionBlock(
                        actions=[
                            CallExpr(name='attack', args=[NameExpr(name='allies'), NameExpr(name='base')]),
                        ],
                    ),
                ),
                Phase(id='win', purpose='Confirm the objective', terminal='success'),
                Phase(id='fail_watch', purpose='Observe allied defeat'),
                Phase(id='loss', purpose='Record failure', terminal='failure'),
            ],
            transitions=[
                Transition(
                    id='arrival',
                    source='approach_watch',
                    target='ready',
                    event=CallExpr(name='enter', args=[NameExpr(name='allies'), NameExpr(name='gate')]),
                    guard=CallExpr(name='alive', args=[NameExpr(name='allies')]),
                    actions=None,
                    priority=10,
                ),
                Transition(
                    id='attrition',
                    source='losses_watch',
                    target='ready',
                    event=CallExpr(name='unit_died', args=[NameExpr(name='guards')]),
                    guard=NameExpr(name='losses_observed'),
                    actions=None,
                    priority=10,
                ),
                Transition(
                    id='release',
                    source='ready',
                    target='exploit',
                    event=None,
                    guard=BinaryExpr(
                        op='and',
                        left=BinaryExpr(
                            op='and',
                            left=CallExpr(name='in_region', args=[NameExpr(name='allies'), NameExpr(name='gate')]),
                            right=NameExpr(name='losses_observed'),
                        ),
                        right=CallExpr(name='alive', args=[NameExpr(name='allies')]),
                    ),
                    actions=None,
                    priority=10,
                ),
                Transition(
                    id='finish',
                    source='exploit',
                    target='win',
                    event=None,
                    guard=BinaryExpr(
                        op='and',
                        left=CallExpr(name='destroyed', args=[NameExpr(name='base')]),
                        right=UnaryExpr(
                            op='not',
                            operand=UnaryExpr(op='not', operand=CallExpr(name='alive', args=[NameExpr(name='allies')])),
                        ),
                    ),
                    actions=None,
                    priority=10,
                ),
                Transition(
                    id='lose',
                    source='fail_watch',
                    target='loss',
                    event=None,
                    guard=UnaryExpr(op='not', operand=CallExpr(name='alive', args=[NameExpr(name='allies')])),
                    actions=None,
                    priority=0,
                ),
            ],
        ),
        backend='sc2',
        bindings=[
            Binding(
                name='allies',
                value=BindingCall(
                    name='unit_group',
                    args=[
                        BindingArg(name='owner', value=1.0),
                        BindingArg(name='unit_type', value='Marine'),
                        BindingArg(name='count', value=4.0),
                        BindingArg(
                            name='spawn',
                            value=BindingCall(
                                name='point_xy',
                                args=[
                                    BindingArg(name=None, value=25.96),
                                    BindingArg(name=None, value=38.5798),
                                ],
                            ),
                        ),
                    ],
                ),
            ),
            Binding(
                name='guards',
                value=BindingCall(
                    name='unit_group',
                    args=[
                        BindingArg(name='owner', value=2.0),
                        BindingArg(name='unit_type', value='Zealot'),
                        BindingArg(name='count', value=3.0),
                        BindingArg(
                            name='spawn',
                            value=BindingCall(
                                name='point_xy',
                                args=[
                                    BindingArg(name=None, value=36.7597),
                                    BindingArg(name=None, value=49.73),
                                ],
                            ),
                        ),
                    ],
                ),
            ),
            Binding(
                name='base',
                value=BindingCall(
                    name='unit',
                    args=[
                        BindingArg(name='owner', value=2.0),
                        BindingArg(name='unit_type', value='Nexus'),
                        BindingArg(
                            name='at',
                            value=BindingCall(
                                name='point_xy',
                                args=[
                                    BindingArg(name=None, value=54.99),
                                    BindingArg(name=None, value=47.18),
                                ],
                            ),
                        ),
                    ],
                ),
            ),
            Binding(
                name='gate',
                value=BindingCall(
                    name='circle',
                    args=[
                        BindingArg(
                            name='center',
                            value=BindingCall(
                                name='point_xy',
                                args=[
                                    BindingArg(name=None, value=54.99),
                                    BindingArg(name=None, value=47.18),
                                ],
                            ),
                        ),
                        BindingArg(name='radius', value=8.0),
                    ],
                ),
            ),
            Binding(
                name='__setup__',
                value=BindingCall(name='setup', args=[BindingArg(name='terminal_policy', value='first_wins')]),
            ),
        ],
    )
    assert strategy.name == 'JoinAndCounter'

def test_event_redeploy():
    strategy = Strategy(
        name='EventRedeploy',
        world=[
            EntityDecl(
                kind='force',
                name='allies',
                properties={'side': 'ally', 'role': 'main_attack'},
            ),
            EntityDecl(
                kind='force',
                name='guards',
                properties={'side': 'enemy', 'role': 'mobile_defense'},
            ),
            EntityDecl(kind='asset', name='base', properties={'side': 'enemy', 'role': 'critical'}),
            EntityDecl(kind='region', name='gate', properties={'role': 'observation_zone'}),        
        ],
        initial=[],
        intent=Intent(
            pattern=None,
            primary=CallExpr(name='destroyed', args=[NameExpr(name='base')]),
            secondary=None,
            success=CallExpr(name='destroyed', args=[NameExpr(name='base')]),
            failure=UnaryExpr(op='not', operand=CallExpr(name='alive', args=[NameExpr(name='allies')])),
        ),
        derived=[],
        plan=Plan(
            start=['approach', 'fail_watch'],
            nodes=[
                Phase(
                    id='approach',
                    purpose='Approach the observation zone',
                    actors=['allies'],
                    focus=['base'],
                    actions=ActionBlock(
                        actions=[
                            CallExpr(name='move', args=[NameExpr(name='allies'), NameExpr(name='gate')]),
                        ],
                    ),
                ),
                Phase(
                    id='exploit',
                    purpose='Attack while observing the result',
                    actors=['allies'],
                    focus=['base'],
                    actions=ActionBlock(
                        actions=[
                            CallExpr(name='attack', args=[NameExpr(name='allies'), NameExpr(name='base')]),
                        ],
                    ),
                ),
                Phase(id='win', purpose='Confirm the objective', terminal='success'),
                Phase(id='fail_watch', purpose='Observe allied defeat'),
                Phase(id='loss', purpose='Record failure', terminal='failure'),
            ],
            transitions=[
                Transition(
                    id='react',
                    source='approach',
                    target='exploit',
                    event=CallExpr(name='enter', args=[NameExpr(name='allies'), NameExpr(name='gate')]),
                    guard=CallExpr(name='alive', args=[NameExpr(name='allies')]),
                    actions=ActionBlock(
                        actions=[
                            CallExpr(name='retarget', args=[NameExpr(name='guards'), NameExpr(name='base')]),
                        ],
                    ),
                    priority=10,
                ),
                Transition(
                    id='finish',
                    source='exploit',
                    target='win',
                    event=None,
                    guard=BinaryExpr(
                        op='and',
                        left=CallExpr(name='destroyed', args=[NameExpr(name='base')]),
                        right=UnaryExpr(
                            op='not',
                            operand=UnaryExpr(op='not', operand=CallExpr(name='alive', args=[NameExpr(name='allies')])),
                        ),
                    ),
                    actions=None,
                    priority=10,
                ),
                Transition(
                    id='lose',
                    source='fail_watch',
                    target='loss',
                    event=None,
                    guard=UnaryExpr(op='not', operand=CallExpr(name='alive', args=[NameExpr(name='allies')])),
                    actions=None,
                    priority=0,
                ),
            ],
        ),
        backend='sc2',
        bindings=[
            Binding(
                name='allies',
                value=BindingCall(
                    name='unit_group',
                    args=[
                        BindingArg(name='owner', value=1.0),
                        BindingArg(name='unit_type', value='Marine'),
                        BindingArg(name='count', value=4.0),
                        BindingArg(
                            name='spawn',
                            value=BindingCall(
                                name='point_xy',
                                args=[
                                    BindingArg(name=None, value=25.96),
                                    BindingArg(name=None, value=38.5798),
                                ],
                            ),
                        ),
                    ],
                ),
            ),
            Binding(
                name='guards',
                value=BindingCall(
                    name='unit_group',
                    args=[
                        BindingArg(name='owner', value=2.0),
                        BindingArg(name='unit_type', value='Zealot'),
                        BindingArg(name='count', value=3.0),
                        BindingArg(
                            name='spawn',
                            value=BindingCall(
                                name='point_xy',
                                args=[
                                    BindingArg(name=None, value=36.7597),
                                    BindingArg(name=None, value=49.73),
                                ],
                            ),
                        ),
                    ],
                ),
            ),
            Binding(
                name='base',
                value=BindingCall(
                    name='unit',
                    args=[
                        BindingArg(name='owner', value=2.0),
                        BindingArg(name='unit_type', value='Nexus'),
                        BindingArg(
                            name='at',
                            value=BindingCall(
                                name='point_xy',
                                args=[
                                    BindingArg(name=None, value=54.99),
                                    BindingArg(name=None, value=47.18),
                                ],
                            ),
                        ),
                    ],
                ),
            ),
            Binding(
                name='gate',
                value=BindingCall(
                    name='circle',
                    args=[
                        BindingArg(
                            name='center',
                            value=BindingCall(
                                name='point_xy',
                                args=[
                                    BindingArg(name=None, value=54.99),
                                    BindingArg(name=None, value=47.18),
                                ],
                            ),
                        ),
                        BindingArg(name='radius', value=8.0),
                    ],
                ),
            ),
            Binding(
                name='__setup__',
                value=BindingCall(name='setup', args=[BindingArg(name='terminal_policy', value='first_wins')]),
            ),
        ],
    )
    assert strategy.name == 'EventRedeploy'


CASES = Path(__file__).with_name("cases")


def case_files(items):
    """Yield case ``.py`` files. A directory contributes its ``*.py`` files in name order."""
    for item in items:
        path = Path(item)
        if path.is_dir():
            yield from sorted(p for p in path.glob("*.py") if p.name != "__init__.py")
        else:
            yield path


def load_strategy(path: Path):
    namespace = {"__file__": str(path)}
    exec(path.read_text(encoding="utf-8"), namespace)
    return namespace["strategy"]


def source_of(path: Path):
    first = path.read_text(encoding="utf-8").splitlines()[0]
    if first.startswith("# source: "):
        return first.removeprefix("# source: ").strip()
    return None


_KINDS = {"force", "asset", "region", "route"}
_SIDES = {"ally", "enemy", "neutral"}
_POLICIES = {"all", "any", "atleast"}
_TERMINALS = {"success", "failure"}
_MODES = {"sequence", "parallel"}


def shape_errors(strategy) -> list[str]:
    """Structural obligations of a Strategy. Independent of how the tree was parsed."""
    errors = []
    names = []
    for entity in strategy.world:
        if entity.kind not in _KINDS:
            errors.append(f"entity {entity.name!r} has kind {entity.kind!r}")
        if entity.name in names:
            errors.append(f"duplicate entity {entity.name!r}")
        names.append(entity.name)
        side = entity.properties.get("side")
        if side is not None and side not in _SIDES:
            errors.append(f"entity {entity.name!r} has side {side!r}")

    nodes = {}
    for node in strategy.plan.nodes:
        if node.id in nodes:
            errors.append(f"duplicate plan node {node.id!r}")
        nodes[node.id] = node
        if isinstance(node, Join):
            if node.policy not in _POLICIES:
                errors.append(f"join {node.id!r} has policy {node.policy!r}")
            if node.policy == "atleast" and node.quorum is None:
                errors.append(f"join {node.id!r} has no quorum")
            continue
        if isinstance(node, Place):   # v0.6 resource place: no actions, no terminal
            if node.tokens < 0:
                errors.append(f"place {node.id!r} has negative initial tokens")
            if node.capacity is not None and not 0 <= node.tokens <= node.capacity:
                errors.append(f"place {node.id!r} has {node.tokens} tokens over capacity {node.capacity}")
            continue
        if node.terminal is not None and node.terminal not in _TERMINALS:
            errors.append(f"phase {node.id!r} has terminal {node.terminal!r}")
        if node.actions is not None and node.actions.mode not in _MODES:
            errors.append(f"phase {node.id!r} has action mode {node.actions.mode!r}")

    if not strategy.plan.start:
        errors.append("plan has no start")
    seen_starts = set()
    for start in strategy.plan.start:
        if start in seen_starts:
            errors.append(f"duplicate start {start!r}")
        seen_starts.add(start)
        node = nodes.get(start)
        if node is None:
            errors.append(f"start {start!r} is not a plan node")
        elif not isinstance(node, Phase):
            errors.append(f"start {start!r} is not a phase")

    transition_ids = set()
    for transition in strategy.plan.transitions:
        if transition.id in transition_ids:
            errors.append(f"duplicate transition {transition.id!r}")
        transition_ids.add(transition.id)
        for arc in [*transition.inputs, *transition.outputs]:   # v0.6 arcs
            if arc.place not in nodes:
                errors.append(f"transition {transition.id!r} arc place {arc.place!r} is missing")
            if arc.weight < 1 or arc.kind not in ("normal", "read", "inhibit"):
                errors.append(f"transition {transition.id!r} has arc {arc.kind}*{arc.weight} on {arc.place!r}")
        if transition.source not in nodes:
            errors.append(f"transition {transition.id!r} source {transition.source!r} is missing")
        if transition.target not in nodes:
            errors.append(f"transition {transition.id!r} target {transition.target!r} is missing")
        if transition.event is None and transition.guard is None:
            errors.append(f"transition {transition.id!r} has neither on nor when")
        if transition.priority < 0:
            errors.append(f"transition {transition.id!r} has negative priority")
        if transition.actions is not None and transition.actions.mode not in _MODES:
            errors.append(f"transition {transition.id!r} has action mode {transition.actions.mode!r}")

    world_names = set(names)
    for binding in strategy.bindings:
        if binding.name.startswith("__"):
            continue
        if binding.name not in world_names:
            errors.append(f"binding {binding.name!r} does not name a world entity")
    return errors


def describe(strategy) -> str:
    return (
        f"{strategy.name}: {len(strategy.world)} entities, "
        f"{len(strategy.plan.nodes)} nodes, {len(strategy.plan.transitions)} transitions, "
        f"start={strategy.plan.start}"
    )


def report(path: Path) -> str:
    built = load_strategy(path)
    line = f"{path.name}  {describe(built)}"
    source = source_of(path)
    if source is None:
        return line
    from stratagemdsl.frontend import parse_file
    from stratagemdsl.paths import REPO_ROOT

    same = built.to_dict() == parse_file(REPO_ROOT / source).to_dict()
    line += "  MATCH" if same else "  DIFFER"
    problems = shape_errors(built)
    if problems:
        line += "  SHAPE " + "; ".join(problems)
    return line


CASE_FILES = sorted(p for p in CASES.glob("*.py")) if CASES.is_dir() else []


@pytest.mark.skipif(not CASE_FILES, reason="no generated cases; run tools/show_ast.py --emit-dir")
@pytest.mark.parametrize("path", CASE_FILES or [Path(".")], ids=lambda path: path.name)
def test_case_file_matches_parsed_source(path):
    built = load_strategy(path)
    source = source_of(path)
    assert source, f"{path.name} has no source comment"
    from stratagemdsl.frontend import parse_file
    from stratagemdsl.paths import REPO_ROOT

    assert built.to_dict() == parse_file(REPO_ROOT / source).to_dict()
    assert shape_errors(built) == []
    print(describe(built))


if __name__ == "__main__":
    inputs = sys.argv[1:] or [CASES]
    for path in case_files(inputs):
        try:
            print(report(path))
        except Exception as exc:
            print(f"{path.name}  ERROR {exc}")