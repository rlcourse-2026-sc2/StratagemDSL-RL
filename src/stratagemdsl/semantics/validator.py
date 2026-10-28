from __future__ import annotations

import itertools
from collections import defaultdict, deque
from typing import Optional

from stratagemdsl.registry.builtins import (
    ACTIONS, EVENTS, FUNCTIONS, ENTITY_KIND_TYPE, Signature, is_subtype,
    EVENT_CONTEXT, PHASE_ARGS, VISIBILITY_SIDES, parse_filter_spec,
)
from stratagemdsl.registry.contracts import REGISTRY
from stratagemdsl.core.diagnostics import DiagnosticBag
from stratagemdsl.semantics.execution import check_execution_semantics
from stratagemdsl.semantics.patterns.checker import PatternChecker
from stratagemdsl.core.ast_utils import binding_arg
from stratagemdsl.registry import extensions as api
from stratagemdsl.core.model import (
    Strategy, Expr, NameExpr, BoolExpr, NumberExpr, StringExpr, CallExpr,
    UnaryExpr, BinaryExpr, Phase, Join, Place, Transition, BindingCall,
)
from stratagemdsl.net import analyze, build_net
from stratagemdsl.net.analysis import UNBOUNDED_CUTOFF


NUMERIC = {"Int", "Float", "Number"}


class Validator:
    def __init__(self, strategy: Strategy, *, strict_sc2: bool = False, backend_probe=None) -> None:
        self.s = strategy
        self.strict_sc2 = strict_sc2
        self.backend_probe = backend_probe
        self.d = DiagnosticBag()
        self.symbol_types: dict[str, str] = {}
        # Set by the plan checks when the plan is well-formed enough to compile.
        self.net = None
        self.net_report = None

    def validate(self) -> DiagnosticBag:
        self._world_symbols()
        self._derived_semantics()
        self._initial_and_intent()
        self._plan()
        self._bindings()
        self._strategic_rules()
        self._pattern_causal_rules()
        if self.strict_sc2 and not self.d.has_errors:
            check_execution_semantics(self.s, self.d, self.backend_probe)
        return self.d

    @property
    def diagnostics(self) -> DiagnosticBag:
        return self.d

    # ------------------------------------------------------------------
    # World / symbol table
    # ------------------------------------------------------------------

    def _world_symbols(self) -> None:
        for e in self.s.world:
            if e.name in self.symbol_types:
                self.d.error("S001_DUP_ENTITY", f"duplicate world entity '{e.name}'")
                continue
            self.symbol_types[e.name] = ENTITY_KIND_TYPE[e.kind]

            if "side" in e.properties:
                side = e.properties["side"]
                if side not in {"ally", "enemy", "neutral"}:
                    self.d.warn(
                        "S010_UNKNOWN_SIDE",
                        f"{e.name}.side is '{side}', expected ally/enemy/neutral",
                    )

    # ------------------------------------------------------------------
    # Expression typing
    # ------------------------------------------------------------------

    def _type_expr(self, e: Expr, context: str = "expression") -> str:
        if isinstance(e, BoolExpr):
            return "Bool"
        if isinstance(e, NumberExpr):
            return "Int" if float(e.value).is_integer() else "Float"
        if isinstance(e, StringExpr):
            return "String"
        if isinstance(e, NameExpr):
            t = self.symbol_types.get(e.name)
            if t is None:
                self.d.error("T001_UNKNOWN_NAME", f"unknown name '{e.name}' in {context}")
                return "Any"
            return t

        if isinstance(e, CallExpr):
            return self._type_function_call(e, context)

        if isinstance(e, UnaryExpr):
            t = self._type_expr(e.operand, context)
            if e.op == "not":
                if not is_subtype(t, "Bool"):
                    self.d.error("T010_EXPECT_BOOL", f"'not' expects Bool, got {t}")
                return "Bool"
            if e.op == "-":
                if t not in NUMERIC:
                    self.d.error("T011_EXPECT_NUMBER", f"unary '-' expects numeric, got {t}")
                return t
            self.d.error("T099_UNKNOWN_UNARY", f"unknown unary operator {e.op}")
            return "Any"

        if isinstance(e, BinaryExpr):
            lt = self._type_expr(e.left, context)
            rt = self._type_expr(e.right, context)

            if e.op in {"+", "-", "*", "/"}:
                if lt not in NUMERIC or rt not in NUMERIC:
                    self.d.error(
                        "T020_ARITH_TYPES",
                        f"operator '{e.op}' expects numeric operands, got {lt} and {rt}",
                    )
                return "Float" if "Float" in {lt, rt} or e.op == "/" else "Int"

            if e.op in {"<", "<=", ">", ">="}:
                if lt not in NUMERIC or rt not in NUMERIC:
                    self.d.error(
                        "T021_COMPARE_TYPES",
                        f"operator '{e.op}' expects numeric operands, got {lt} and {rt}",
                    )
                return "Bool"

            if e.op in {"==", "!="}:
                if not (is_subtype(lt, rt) or is_subtype(rt, lt) or lt == "Any" or rt == "Any"):
                    self.d.error(
                        "T022_EQUALITY_TYPES",
                        f"cannot compare {lt} and {rt} with '{e.op}'",
                    )
                return "Bool"

            if e.op in {"and", "or", "implies"}:
                if not is_subtype(lt, "Bool") or not is_subtype(rt, "Bool"):
                    self.d.error(
                        "T023_BOOL_TYPES",
                        f"operator '{e.op}' expects Bool operands, got {lt} and {rt}",
                    )
                return "Bool"

            self.d.error("T098_UNKNOWN_BINARY", f"unknown binary operator {e.op}")
            return "Any"

        self.d.error("T999_UNKNOWN_EXPR", f"unknown expression node {type(e).__name__}")
        return "Any"

    def _type_function_call(self, call: CallExpr, context: str) -> str:
        sigs = FUNCTIONS.get(call.name)
        if sigs is None:
            self.d.error("T030_UNKNOWN_FUNCTION", f"unknown predicate/metric '{call.name}' in {context}")
            for a in call.args:
                self._type_expr(a, context)
            return "Any"

        arg_types = self._type_call_args(call, f"{context}: {call.name}")
        sig = self._select_signature(call.name, arg_types, sigs, "function")
        if sig is not None:
            self._check_literal_args(call)
            self._check_extension_literals(call)
        time_arg = call.args[0] if call.name == "after" and sig else None
        literal_time = (time_arg.value if isinstance(time_arg, NumberExpr)
                        else -time_arg.operand.value if isinstance(time_arg, UnaryExpr) and
                        time_arg.op == "-" and isinstance(time_arg.operand, NumberExpr) else None)
        if literal_time is not None and literal_time < 0:
            self.d.error("T080_NEGATIVE_TIME", "after(seconds) requires a nonnegative mission-time threshold")
        spec = REGISTRY.get(("function", call.name))
        if spec is not None and spec.alias_of and sig:
            self.d.warn("W110_LEGACY_API", f"{call.name} is a compatibility alias for {spec.alias_of}; {spec.effect_evidence}")
        return sig.returns if sig else "Any"

    def _type_call_args(self, call: CallExpr, context: str) -> list[str]:
        """Phase references occupy a separate namespace from world entities."""
        phase_positions = PHASE_ARGS.get(call.name, ())
        nodes = {n.id: n for n in self.s.plan.nodes} if self.s.plan else {}
        types = []
        for i, arg in enumerate(call.args):
            if i in phase_positions:
                if not isinstance(arg, NameExpr) or arg.name not in nodes:
                    self.d.error("T081_PHASE_REFERENCE", f"{call.name}(...) argument {i + 1} must name an existing plan node")
                    types.append("Any")
                else:
                    # Timers and elapsed() can belong to joins as well as phases.
                    types.append("Phase")
            else:
                types.append(self._type_expr(arg, context))
        return types

    def _check_literal_args(self, call: CallExpr) -> None:
        if call.name == "visible_to" and call.args:
            side = call.args[0]
            if not isinstance(side, StringExpr) or side.value not in VISIBILITY_SIDES:
                self.d.error("T091_VISIBILITY_SIDE", "visible_to(...) needs a literal side: ally or enemy")
        if call.name == "count_matching" and len(call.args) == 2:
            spec = call.args[1]
            if not isinstance(spec, StringExpr):
                self.d.error("T090_FILTER_SPEC", "count_matching(...) filter must be a string literal")
            else:
                for error in parse_filter_spec(spec.value)[2]:
                    self.d.error("T090_FILTER_SPEC", f"count_matching filter: {error}")
        if call.name in {"timer", "window_held", "hold_window", "resume_window", "restart_window"} and len(call.args) > 1:
            duration = call.args[1]
            if not isinstance(duration, NumberExpr) or duration.value <= 0:
                self.d.error("T082_TIMER_DURATION", f"{call.name}(...) needs a positive number literal in seconds")

    def _calls_in(self, expr: Expr | None, expanding: frozenset[str] = frozenset()):
        """Walk nested calls, including references to acyclic derived facts."""
        if isinstance(expr, CallExpr):
            yield expr
            for arg in expr.args:
                yield from self._calls_in(arg, expanding)
        elif isinstance(expr, UnaryExpr):
            yield from self._calls_in(expr.operand, expanding)
        elif isinstance(expr, BinaryExpr):
            yield from self._calls_in(expr.left, expanding)
            yield from self._calls_in(expr.right, expanding)
        elif isinstance(expr, NameExpr) and expr.name not in expanding:
            definition = next((d.expr for d in self.s.derived if d.name == expr.name), None)
            if definition is not None:
                yield from self._calls_in(definition, expanding | {expr.name})

    def _check_event_context(self, expr: Expr | None, event: Optional[CallExpr], label: str) -> None:
        for call in self._calls_in(expr):
            allowed = EVENT_CONTEXT.get(call.name)
            if allowed is not None and (event is None or event.name not in allowed):
                observed = event.name if event else "no event"
                self.d.error("T080_EVENT_CONTEXT", f"{call.name}(...) in {label} has {observed}; use one of {sorted(allowed)}")

    def _check_event_call(self, call: CallExpr) -> None:
        sigs = EVENTS.get(call.name)
        arg_types = self._type_call_args(call, f"event {call.name}")
        if sigs is None:
            self.d.error("T040_UNKNOWN_EVENT", f"unknown event '{call.name}'")
            return
        if self._select_signature(call.name, arg_types, sigs, "event") is not None:
            self._check_literal_args(call)
            self._check_extension_literals(call)

    def _check_action_call(self, call: CallExpr) -> None:
        sigs = ACTIONS.get(call.name)
        arg_types = self._type_call_args(call, f"action {call.name}")
        if sigs is None:
            self.d.error("T050_UNKNOWN_ACTION", f"unknown action '{call.name}'")
            return
        if self._select_signature(call.name, arg_types, sigs, "action") is not None:
            self._check_literal_args(call)
            self._check_extension_literals(call)

    # ------------------------------------------------------------------
    # v0.4 literal vocabularies and memory keys
    # ------------------------------------------------------------------

    def _side_names(self) -> set[str]:
        # This tutorial backend implements exactly two controlled players.
        # Aggregated/custom sides must be implemented across reset, roster and
        # visibility semantics before accepting their names here.
        return set(api.SIDES)

    def _check_extension_literals(self, call: CallExpr) -> None:
        """T091 side names / T101 vocabularies / T090 filters / T110 memory keys."""
        for i, a in enumerate(call.args):
            table = api.VOCAB.get((call.name, i))
            if table is None:
                continue
            if not isinstance(a, StringExpr):
                self.d.error("T101_VOCAB", f"{call.name}(...) argument {i + 1} must be a string literal")
                continue
            if table == "side":
                if a.value not in self._side_names():
                    self.d.error("T091_VISIBILITY_SIDE",
                                 f"{call.name}(...) argument {i + 1}: unknown side \"{a.value}\"; use one of {sorted(self._side_names())}")
            elif a.value not in table:
                self.d.error("T101_VOCAB", f"{call.name}(...) argument {i + 1}: \"{a.value}\" is not one of {sorted(table)}")
        if call.name == "count_matching_vs" and len(call.args) == 3:
            spec = call.args[2]
            if not isinstance(spec, StringExpr):
                self.d.error("T090_FILTER_SPEC", "count_matching_vs(...) filter must be a string literal")
            else:
                for err in api.filter_masks(spec.value)[2]:
                    self.d.error("T090_FILTER_SPEC", f"count_matching_vs filter \"{spec.value}\": {err}")
        if call.name in api.MEMORY or call.name in ("tag", "count_tagged"):
            idx = 1 if call.name in ("tag", "count_tagged") else api.MEMORY_KEY_INDEX.get(call.name, 0)
            k = call.args[idx] if idx < len(call.args) else None
            if not isinstance(k, StringExpr) or not k.value:
                self.d.error("T110_MEMORY_KEY", f"{call.name}(...) key must be a non-empty string literal")

    def _memory_rules(self) -> None:
        """T111 one kind per key, W111 reads of never-written keys, T112 tag slots."""
        calls: list[CallExpr] = []
        for expr in self.s.initial:
            calls += list(self._calls_in(expr))
        if self.s.intent is not None:
            for field in ("primary", "secondary", "success", "failure"):
                calls += list(self._calls_in(getattr(self.s.intent, field)))
        for d in self.s.derived:
            calls += list(self._calls_in(d.expr))
        for t in self.s.plan.transitions:
            calls += list(self._calls_in(t.guard))
            if t.event:
                for arg in t.event.args:
                    calls += list(self._calls_in(arg))
        for n in [*self.s.plan.nodes, *self.s.plan.transitions]:
            if isinstance(n, Phase):
                for field in ("entry", "invariant", "exit"):
                    calls += list(self._calls_in(getattr(n, field)))
            block = getattr(n, "actions", None)
            if block:
                for a in block.actions:
                    calls.append(a)
                    for arg in a.args:
                        calls += list(self._calls_in(arg))
        kinds: dict[str, set[str]] = defaultdict(set)
        written: set[str] = set()
        read: list[tuple[str, str]] = []
        slots: set[str] = set()
        for c in calls:
            if c.name in ("tag", "count_tagged") and len(c.args) > 1 and isinstance(c.args[1], StringExpr):
                slots.add(c.args[1].value)
            if c.name not in api.MEMORY:
                continue
            idx = api.MEMORY_KEY_INDEX.get(c.name, 0)
            k = c.args[idx] if idx < len(c.args) else None
            if not isinstance(k, StringExpr):
                continue
            kind, mode = api.MEMORY[c.name]
            if kind != "*":
                kinds[k.value].add(kind)
            if mode == "w":
                written.add(k.value)
            elif mode == "r":
                read.append((c.name, k.value))
        for k, ks in sorted(kinds.items()):
            if len(ks) > 1:
                self.d.error("T111_MEMORY_KIND", f"memory key \"{k}\" is used as {sorted(ks)}; one key holds one kind")
        for name, k in sorted(set(read)):
            if k not in written:
                self.d.warn("W111_MEMORY_UNWRITTEN", f"{name}(\"{k}\") reads a key nothing writes; it always sees the default")
        if len(slots) > 64:
            self.d.error("T112_TAG_SLOTS", f"{len(slots)} tag slots used; at most 64")

    def _select_signature(
        self, name: str, actual: list[str], sigs: list[Signature], namespace: str
    ) -> Optional[Signature]:
        arity_matches = [s for s in sigs if len(s.args) == len(actual)]
        if not arity_matches:
            expected = sorted({len(s.args) for s in sigs})
            self.d.error(
                "T060_ARITY",
                f"{namespace} '{name}' expects arity {expected}, got {len(actual)}",
            )
            return None

        for sig in arity_matches:
            if all(is_subtype(a, e) for a, e in zip(actual, sig.args)):
                return sig

        options = " or ".join("(" + ", ".join(s.args) + ")" for s in arity_matches)
        self.d.error(
            "T061_ARGUMENT_TYPES",
            f"{namespace} '{name}' got ({', '.join(actual)}), expected {options}",
        )
        return None

    def _check_action_event_context(self, a: CallExpr, event: Optional[CallExpr], label: str) -> None:
        """v0.4: event-context functions in action arguments, and
        remember_event_unit, need the enclosing transition's event."""
        for arg in a.args:
            self._check_event_context(arg, event, label)
        if a.name == "remember_event_unit":
            role = a.args[1].value if len(a.args) > 1 and isinstance(a.args[1], StringExpr) else None
            if event is None:
                self.d.error("T080_EVENT_CONTEXT", f"remember_event_unit(...) in {label} needs a transition with an 'on' event")
            elif event.name not in api.UNIT_EVENTS:
                self.d.error("T080_EVENT_CONTEXT", f"remember_event_unit(...) in {label}: event '{event.name}' has no event unit")
            elif role == "source" and event.name not in {"unit_died", "unit_damaged", "effect_used", "unit_healed"}:
                self.d.error("T080_EVENT_CONTEXT", f"remember_event_unit(..., \"source\") in {label}: event '{event.name}' has no source unit")

    def _require_bool(self, e: Expr, label: str) -> None:
        t = self._type_expr(e, label)
        if not is_subtype(t, "Bool"):
            self.d.error("T070_BOOL_CONTEXT", f"{label} must be Bool, got {t}")

    # ------------------------------------------------------------------
    # Scenario-local derived strategic facts
    # ------------------------------------------------------------------

    def _derived_semantics(self) -> None:
        derived_names = {d.name for d in self.s.derived}

        # Declare names first; infer their types after visiting dependencies.
        for d in self.s.derived:
            if d.name in self.symbol_types:
                self.d.error(
                    "D001_DERIVED_SHADOWS_SYMBOL",
                    f"derived fact '{d.name}' shadows an existing symbol",
                )
            else:
                self.symbol_types[d.name] = "Any"

        # Reject recursive/cyclic derived facts in v0.2.
        deps: dict[str, set[str]] = {n: set() for n in derived_names}
        for d in self.s.derived:
            deps[d.name] = self._name_dependencies(d.expr) & derived_names

        color = {n: 0 for n in derived_names}
        ordered: list[str] = []

        def dfs(u: str) -> bool:
            color[u] = 1
            for v in deps[u]:
                if color[v] == 1:
                    return True
                if color[v] == 0 and dfs(v):
                    return True
            color[u] = 2
            ordered.append(u)
            return False

        for n in derived_names:
            if color[n] == 0 and dfs(n):
                self.d.error(
                    "D002_DERIVED_CYCLE",
                    "derived expressions must be acyclic",
                )
                return

        definitions = {d.name: d.expr for d in self.s.derived}
        for name in ordered:
            inferred = self._type_expr(definitions[name], f"derive {name}")
            if inferred not in {"Bool", "Int", "Float", "Any"}:
                self.d.error("D003_DERIVED_TYPE", f"derive {name} must yield Bool/Int/Float, got {inferred}")
            self.symbol_types[name] = inferred

    def _name_dependencies(self, e: Expr) -> set[str]:
        out: set[str] = set()

        def walk(x: Expr):
            if isinstance(x, NameExpr):
                out.add(x.name)
            elif isinstance(x, CallExpr):
                for a in x.args:
                    walk(a)
            elif isinstance(x, UnaryExpr):
                walk(x.operand)
            elif isinstance(x, BinaryExpr):
                walk(x.left)
                walk(x.right)

        walk(e)
        return out

    # ------------------------------------------------------------------
    # Initial / intent
    # ------------------------------------------------------------------

    def _initial_and_intent(self) -> None:
        for e in self.s.initial:
            self._require_bool(e, "initial fact")
            self._check_event_context(e, None, "initial fact")

        if self.s.intent is None:
            self.d.error("I001_MISSING_INTENT", "strategy has no intent section")
            return

        self._require_bool(self.s.intent.primary, "intent.primary")
        if self.s.intent.secondary is not None:
            self._require_bool(self.s.intent.secondary, "intent.secondary")
        self._require_bool(self.s.intent.success, "intent.success")
        self._require_bool(self.s.intent.failure, "intent.failure")
        for field in ("primary", "secondary", "success", "failure"):
            self._check_event_context(getattr(self.s.intent, field), None, f"intent.{field}")

    # ------------------------------------------------------------------
    # PlanGraph checks
    # ------------------------------------------------------------------

    def _plan(self) -> None:
        p = self.s.plan
        if p is None:
            self.d.error("P001_MISSING_PLAN", "strategy has no plan section")
            return

        nodes: dict[str, Phase | Join | Place] = {}
        for n in p.nodes:
            if n.id in nodes:
                self.d.error("P002_DUP_NODE", f"duplicate plan node '{n.id}'")
            else:
                nodes[n.id] = n

        if not p.start:
            self.d.error("P003_NO_START", "plan must declare at least one start phase")
        seen_starts: set[str] = set()
        for start_id in p.start:
            if start_id in seen_starts:
                # A repeated start id is an authoring mistake: every initial
                # cascade would run once per copy, so an all/atleast join
                # could be satisfied by copies of the same arrival.
                self.d.error("P006_DUP_START", f"duplicate start phase '{start_id}'")
            seen_starts.add(start_id)
            if start_id not in nodes:
                self.d.error("P003_START_NOT_FOUND", f"start node '{start_id}' does not exist")
            elif not isinstance(nodes[start_id], Phase):
                hint = "; give a place its tokens with `initial N;`" if isinstance(nodes[start_id], Place) else ""
                self.d.error("P004_START_NOT_PHASE", f"start node '{start_id}' must be a phase{hint}")

        # v0.6 token places
        for n in p.nodes:
            if not isinstance(n, Place):
                continue
            if n.capacity is not None and n.capacity < 1:
                self.d.error("P050_PLACE_CAPACITY", f"place '{n.id}' capacity must be at least 1")
            if n.tokens < 0 or (n.capacity is not None and n.tokens > n.capacity):
                self.d.error("P050_PLACE_CAPACITY",
                             f"place '{n.id}' starts with {n.tokens} tokens but its capacity is {n.capacity}")
        for n in p.nodes:
            if isinstance(n, Phase) and n.repeatable and n.terminal:
                self.d.error("P052_REPEATABLE_TERMINAL", f"terminal phase '{n.id}' cannot be repeatable")

        trans_ids: set[str] = set()
        outgoing: dict[str, list[Transition]] = defaultdict(list)   # consumed place -> transitions
        incoming: dict[str, list[Transition]] = defaultdict(list)   # produced place -> transitions
        readers: dict[str, list[Transition]] = defaultdict(list)    # read/inhibit place -> transitions

        for t in p.transitions:
            if t.id in trans_ids:
                self.d.error("P005_DUP_TRANSITION", f"duplicate transition '{t.id}'")
            trans_ids.add(t.id)

            if t.source not in nodes:
                self.d.error("P006_BAD_SOURCE", f"transition '{t.id}' source '{t.source}' not found")
            if t.target not in nodes:
                self.d.error("P007_BAD_TARGET", f"transition '{t.id}' target '{t.target}' not found")
            self._arc_rules(t, nodes)

            for a in t.inputs:
                if a.kind == "normal":
                    outgoing[a.place].append(t)
                else:
                    readers[a.place].append(t)
            for a in t.outputs:
                incoming[a.place].append(t)

            if t.priority < 0:
                self.d.error("P008_NEG_PRIORITY", f"transition '{t.id}' has negative priority")

            if t.event is None and t.guard is None:
                self.d.error(
                    "P010_NO_TRIGGER",
                    f"transition '{t.id}' needs at least 'on' or 'when'",
                )
            if t.event is not None:
                self._check_event_call(t.event)
                for arg in t.event.args:
                    self._check_event_context(arg, None, f"transition {t.id}.on")
            if t.guard is not None:
                self._require_bool(t.guard, f"transition {t.id}.when")
                self._check_event_context(t.guard, t.event, f"transition {t.id}.when")
            if t.actions:
                for a in t.actions.actions:
                    self._check_action_call(a)
                    self._check_action_event_context(a, t.event, f"transition {t.id}.do")

        # P009: transitions competing for one token need distinct priorities.
        # In v0.2 that is "one source, one priority"; with arcs, every place
        # two transitions consume from is a conflict.
        for place in nodes:
            by_priority: dict[int, list[str]] = defaultdict(list)
            for t in outgoing.get(place, []):
                by_priority[t.priority].append(t.id)
            for prio, ids in sorted(by_priority.items()):
                if len(ids) > 1:
                    self.d.error("P009_DUP_PRIORITY", f"source '{place}' has duplicate priority {prio}")

        # phase-local semantics
        for n in p.nodes:
            if isinstance(n, Phase):
                if not n.purpose.strip():
                    self.d.error("P011_EMPTY_PURPOSE", f"phase '{n.id}' has empty purpose")
                for a in n.actors:
                    ty = self.symbol_types.get(a)
                    if ty is None:
                        self.d.error("P012_UNKNOWN_ACTOR", f"phase '{n.id}' actor '{a}' not found")
                    elif not is_subtype(ty, "Force"):
                        self.d.error(
                            "P013_ACTOR_NOT_FORCE",
                            f"phase '{n.id}' actor '{a}' is {ty}, expected Force",
                        )
                for f in n.focus:
                    ty = self.symbol_types.get(f)
                    if ty is None:
                        self.d.error("P014_UNKNOWN_FOCUS", f"phase '{n.id}' focus '{f}' not found")
                    elif not (is_subtype(ty, "Entity") or is_subtype(ty, "Location")):
                        self.d.error(
                            "P014_FOCUS_TYPE",
                            f"phase '{n.id}' focus '{f}' has type {ty}, expected Entity or Location",
                        )

                if n.entry is not None:
                    self._require_bool(n.entry, f"phase {n.id}.entry")
                    self._check_event_context(n.entry, None, f"phase {n.id}.entry")
                if n.invariant is not None:
                    self._require_bool(n.invariant, f"phase {n.id}.invariant")
                    self._check_event_context(n.invariant, None, f"phase {n.id}.invariant")
                if n.exit is not None:
                    self._require_bool(n.exit, f"phase {n.id}.exit")
                    self._check_event_context(n.exit, None, f"phase {n.id}.exit")
                if n.actions:
                    for a in n.actions.actions:
                        self._check_action_call(a)
                        self._check_action_event_context(a, None, f"phase {n.id}.do")

                if n.terminal is not None and (outgoing.get(n.id) or readers.get(n.id)):
                    self.d.error(
                        "P015_TERMINAL_OUTGOING",
                        f"terminal phase '{n.id}' must not have outgoing transitions",
                    )
                if n.terminal is None and not outgoing.get(n.id):
                    self.d.warn(
                        "P016_NONTERMINAL_DEAD_END",
                        f"non-terminal phase '{n.id}' has no outgoing transition",
                    )

        # join semantics
        for n in p.nodes:
            if not isinstance(n, Join):
                continue
            indeg = len(incoming.get(n.id, []))
            outdeg = len(outgoing.get(n.id, []))
            if indeg == 0:
                self.d.error("P020_JOIN_NO_INPUT", f"join '{n.id}' has no incoming transitions")
            if outdeg != 1:
                self.d.error(
                    "P021_JOIN_OUTDEGREE",
                    f"join '{n.id}' must have exactly one outgoing transition in v0.2, got {outdeg}",
                )
            if n.policy == "atleast":
                if n.quorum is None or not (1 <= n.quorum <= indeg):
                    self.d.error(
                        "P022_BAD_QUORUM",
                        f"join '{n.id}' quorum must satisfy 1 <= q <= indegree({indeg}), got {n.quorum}",
                    )

        self._memory_rules()
        self._reachability(nodes)
        self._acyclic(nodes)
        if not any(d.code.startswith(("P00", "P04", "P05")) and d.severity == "error" for d in self.d.items):
            self._net_rules(nodes, incoming)

    def _arc_rules(self, t: Transition, nodes) -> None:
        """v0.6 arc well-formedness (the v0.2 single-arc form always passes)."""
        if not any(a.kind == "normal" for a in t.inputs):
            self.d.error("P044_NO_CONSUME",
                         f"transition '{t.id}' must consume a token from at least one input place")
        for side, arcs in (("input", t.inputs), ("output", t.outputs)):
            seen: set[tuple[str, str]] = set()
            for a in arcs:
                if a.place not in nodes and a.place not in (t.source, t.target):
                    self.d.error("P040_BAD_ARC", f"transition '{t.id}' {side} arc '{a.place}' not found")
                if (a.place, a.kind) in seen:
                    self.d.error("P043_DUP_ARC", f"transition '{t.id}' lists {side} '{a.place}' twice")
                seen.add((a.place, a.kind))
                if a.weight < 1:
                    self.d.error("P042_ARC_WEIGHT", f"transition '{t.id}' arc '{a.place}' needs weight >= 1")
                if side == "output" and a.kind != "normal":
                    self.d.error("P041_ARC_KIND",
                                 f"transition '{t.id}' output '{a.place}' cannot be a read/inhibitor arc")
                node = nodes.get(a.place)
                if isinstance(node, (Phase, Join)) and a.weight != 1 and a.kind != "inhibit":
                    self.d.error("P042_ARC_WEIGHT",
                                 f"transition '{t.id}' arc '{a.place}': phases and joins hold one token, use weight 1")
                if isinstance(node, Join) and a.kind != "normal":
                    self.d.error("P041_ARC_KIND",
                                 f"transition '{t.id}' cannot read or inhibit join '{a.place}'; test the phase after it")

    def _plan_edges(self) -> dict[str, set[str]]:
        """DSL-level place graph: an input place (normal or read) reaches every output."""
        edges: dict[str, set[str]] = defaultdict(set)
        for t in self.s.plan.transitions:
            for a in t.inputs:
                if a.kind == "inhibit":
                    continue
                for b in t.outputs:
                    edges[a.place].add(b.place)
        return edges

    def _reachability(self, nodes) -> None:
        roots = [s for s in self.s.plan.start if s in nodes]
        roots += [n.id for n in self.s.plan.nodes if isinstance(n, Place) and n.tokens > 0]
        if not roots:
            return
        edges = self._plan_edges()
        seen = set()
        q = deque(roots)
        while q:
            u = q.popleft()
            if u in seen:
                continue
            seen.add(u)
            for v in edges.get(u, ()):
                if v in nodes:
                    q.append(v)
        for n in nodes:
            if n not in seen:
                self.d.error("P030_UNREACHABLE", f"plan node '{n}' is unreachable from start")

    def _acyclic(self, nodes) -> None:
        """A cycle can only repeat through repeatable phases or token places.

        v0.2 plans (no `repeatable`, no `place`) therefore stay acyclic,
        exactly as before; v0.6 loops must say which node re-enters.
        """
        edges = self._plan_edges()
        color = {n: 0 for n in nodes}
        stack: list[str] = []
        cycles: list[list[str]] = []

        def dfs(u: str) -> None:
            color[u] = 1
            stack.append(u)
            for v in sorted(edges.get(u, ())):
                if v not in color:
                    continue
                if color[v] == 1:
                    cycles.append(stack[stack.index(v):] + [v])
                elif color[v] == 0:
                    dfs(v)
            stack.pop()
            color[u] = 2

        for n in nodes:
            if color[n] == 0:
                dfs(n)
        for cycle in cycles:
            reentrant = [x for x in cycle if (isinstance(nodes.get(x), Phase) and nodes[x].repeatable)
                         or isinstance(nodes.get(x), Place)]
            if not reentrant:
                self.d.error(
                    "P031_CYCLE",
                    f"plan cycle {' -> '.join(cycle)} only passes once-per-round phases, so it can never "
                    f"repeat; mark a phase on it `repeatable` (v0.6) or use backend repetition inside a phase",
                )
                return

    def _net_rules(self, nodes, incoming) -> None:
        """Reachability-graph checks on the compiled Petri net (net layer).

        P023 keeps its v0.2 meaning -- an all/atleast(k>1) join that no run
        can complete -- but is now decided on the net's state space instead
        of by enumerating fork choices.
        """
        net = build_net(self.s)
        report = analyze(net)
        self.net, self.net_report = net, report
        fired = report.fired()
        marked = report.marked()
        for cycle in report.immediate_cycles:
            self.d.error("N030_IMMEDIATE_CYCLE",
                         f"immediate transitions form a cycle through {' -> '.join(cycle)}; the token game "
                         f"would never settle -- give one transition an event or a live guard")
        if report.immediate_cycles:
            return   # the state space is meaningless while a settle cannot end
        for c in report.components:
            for pid in sorted(c.unbounded):
                self.d.error("N001_UNBOUNDED_PLACE",
                             f"place '{pid}' can exceed {UNBOUNDED_CUTOFF} tokens; declare `capacity` "
                             f"(witness: {', '.join(c.unbounded[pid][-6:]) or 'start'})")
            if c.zeno:
                self.d.error("N030_IMMEDIATE_CYCLE", f"settling the marking did not terminate: {c.zeno}")
        if not report.complete:
            self.d.warn("N002_STATE_LIMIT",
                        "the plan net's state space exceeds the analysis limit; net proofs below are partial")

        dead_joins: set[str] = set()
        for n in self.s.plan.nodes:
            if not isinstance(n, Join) or n.policy == "any":
                continue
            join_incoming = incoming.get(n.id, [])
            threshold = len(join_incoming) if n.policy == "all" else (n.quorum or 1)
            if threshold <= 1 or len(join_incoming) < threshold:
                continue
            if f"{n.id}.sync" not in fired and report.complete:
                dead_joins.add(n.id)
                self.d.error(
                    "P023_JOIN_DEADLOCK",
                    f"join '{n.id}' (policy {n.policy}, needs {threshold} distinct arrivals) can never "
                    f"complete: no reachable marking of the plan net supplies enough of its incoming "
                    f"edges ({sorted(jt.id for jt in join_incoming)}) -- the branches compete for one "
                    f"token; give them genuinely independent starting points (e.g. separate entries in "
                    f"`plan.start`) or a fork transition with several outputs",
                )
        if not report.complete:
            return
        structurally_unreachable = {d.message.split("'")[1] for d in self.d.items if d.code == "P030_UNREACHABLE"}
        for n in self.s.plan.nodes:
            if n.id in marked or n.id in structurally_unreachable:
                continue
            self.d.warn("N011_NEVER_MARKED",
                        f"plan node '{n.id}' is structurally reachable but no run of the plan net marks it"
                        + (f" (join '{n.id}' never completes)" if n.id in dead_joins else ""))
        for t in net.transitions:
            if t.silent or t.id in fired:
                continue
            if all(pl in marked for pl in t.consumed):
                shadow = next((u for u in sorted(net.transitions, key=lambda x: x.rank)
                               if u is not t and u.guard_static is True and u.rank < t.rank
                               and net.in_conflict(t, u) and (u.trigger == t.trigger or u.dispatch == "immediate")), None)
                why = ("its guard is constant false" if t.guard_static is False else
                       f"'{shadow.id}' outranks it on the same token and its guard is always true" if shadow else
                       "its input places are never marked together, or a higher-ranked transition always takes the token first")
                self.d.warn("N010_DEAD_TRANSITION", f"transition '{t.id}' can never fire: {why}")
        for c in report.components:
            for tid in sorted(c.blocked):
                self.d.warn("N020_CAPACITY_BLOCKED",
                            f"transition '{tid}' can be blocked because an output place is full "
                            f"(witness: {', '.join(c.blocked[tid][-6:]) or 'start'})")
        stuck = report.global_stuck()
        if stuck:
            where = "; ".join(", ".join(sorted(s["marking"])) or "empty marking" for s in stuck)
            self.d.warn("N040_DEADLOCK",
                        f"the plan can stop with no terminal result: tokens on [{where}] enable no transition")
        success = [pid for pid, kind in net.terminals().items() if kind == "success"]
        if success and not any(pid in report.terminal_reached() for pid in success):
            self.d.warn("N050_NO_SUCCESS_PATH", "no run of the plan net reaches a success terminal")

    # ------------------------------------------------------------------
    # Backend binding validation
    # ------------------------------------------------------------------

    def _bindings(self) -> None:
        if self.s.backend is None:
            self.d.warn("B001_NO_BACKEND", "no binding section; strategy is analyzable but not executable")
            return

        by_name = {}
        for b in self.s.bindings:
            if b.name in by_name:
                self.d.error("B002_DUP_BINDING", f"duplicate binding for '{b.name}'")
            by_name[b.name] = b

        for e in self.s.world:
            if e.name not in by_name:
                self.d.error(
                    "B003_MISSING_BINDING",
                    f"executable world entity '{e.name}' ({e.kind}) has no {self.s.backend} binding",
                )
                continue

            value = by_name[e.name].value
            if not isinstance(value, BindingCall):
                self.d.error(
                    "B004_BINDING_CALL_EXPECTED",
                    f"binding for '{e.name}' must be a constructor call",
                )
                continue

            allowed = {
                "force": {"unit_group", "dynamic_group", "group_slice"},
                "asset": {"unit", "structure", "dynamic_unit", "unit_group"},
                "region": {"circle", "region_id", "polygon", "rect", "union", "whole_map"},
                "route": {"route"},
            }[e.kind]
            if value.name not in allowed:
                self.d.error(
                    "B005_BINDING_KIND",
                    f"{e.kind} '{e.name}' must bind with one of {sorted(allowed)}, got '{value.name}'",
                )

        setup = by_name.get("__setup__")
        if setup is not None:
            if not isinstance(setup.value, BindingCall) or setup.value.name != "setup":
                self.d.error("B008_BAD_SETUP", "__setup__ must bind with setup(...)")
            else:
                seen_keys = set()
                for arg in setup.value.args:
                    if arg.name is None or arg.name in seen_keys:
                        self.d.error("B008_BAD_SETUP", "setup options must be named and occur once")
                    seen_keys.add(arg.name)
                    if arg.name == "terminal_policy" and (not isinstance(arg.value, str) or arg.value not in {"first_wins", "legacy"}):
                        self.d.error("B008_BAD_SETUP", 'setup terminal_policy must be "first_wins" or "legacy"')
                    elif arg.name == "poll_period":
                        value = arg.value
                        if isinstance(value, bool) or not isinstance(value, (int, float)) or not (0.0625 <= float(value) <= 60):
                            self.d.error("B008_BAD_SETUP", "setup poll_period must be a number of seconds in [0.0625, 60]")
                    elif arg.name in ("fog", "allow_rewrite") and not isinstance(arg.value, bool):
                        self.d.error("B008_BAD_SETUP", f"setup {arg.name} must be true or false")
                self._sides_rules(setup.value, by_name)

        # unknown binding targets
        for name in by_name:
            if name == "__setup__":
                continue
            if name not in self.symbol_types:
                self.d.error("B006_UNKNOWN_BINDING_TARGET", f"binding target '{name}' is not a world entity")

    def _sides_rules(self, setup: BindingCall, by_name: dict) -> None:
        """B110 a player belongs to one side; B111 owners match their side."""
        sides = next((a.value for a in setup.args if a.name == "sides"), None)
        if sides is None:
            return
        if not isinstance(sides, list):
            self.d.error("B110_BAD_SIDES", "setup sides must be a list of side constructors")
            return
        owner_of: dict[int, str] = {}
        players_of: dict[str, set[int]] = {}
        for it in sides:
            if not isinstance(it, BindingCall) or it.name != "side":
                self.d.error("B110_BAD_SIDES", "setup sides=[side(\"name\", players=[...]), ...] expected")
                continue
            name, players = binding_arg(it, "name", 0), binding_arg(it, "players", 1)
            if not isinstance(name, str) or not name or not isinstance(players, list) or not players or \
                    not all(isinstance(x, (int, float)) and not isinstance(x, bool) and float(x).is_integer() and 0 <= x <= 15 for x in players):
                self.d.error("B110_BAD_SIDES", "side(\"name\", players=[1, 3]) needs a name and player numbers")
                continue
            if name in players_of or len(set(players)) != len(players):
                self.d.error("B110_BAD_SIDES", f"side '{name}' and its players must occur once")
            if name not in api.SIDES or players != [api.SIDES.get(name)]:
                self.d.error("B112_UNSUPPORTED_SIDES", "this backend supports only side(\"ally\", players=[1]) and side(\"enemy\", players=[2]); custom or aggregate sides need a broader reset/ownership implementation")
            players_of[name] = {int(x) for x in players}
            for pl in players_of[name]:
                if pl in owner_of and owner_of[pl] != name:
                    self.d.error("B110_BAD_SIDES", f"player {pl} is in both sides '{owner_of[pl]}' and '{name}'")
                owner_of[pl] = name
        for e in self.s.world:
            side = e.properties.get("side")
            b = by_name.get(e.name)
            if side not in players_of or b is None or not isinstance(b.value, BindingCall):
                continue
            owner = next((a.value for a in b.value.args if a.name == "owner"), None)
            if isinstance(owner, (int, float)) and not isinstance(owner, bool) and int(owner) not in players_of[side]:
                self.d.error("B111_OWNER_SIDE", f"'{e.name}' is side '{side}' but owner {int(owner)} is not in that side's players")

    # ------------------------------------------------------------------
    # Strategic causal checks
    # ------------------------------------------------------------------

    def _all_action_names(self) -> list[str]:
        out = []
        for n in self.s.plan.nodes:
            if isinstance(n, Phase) and n.actions:
                out.extend(a.name for a in n.actions.actions)
        for t in self.s.plan.transitions:
            if t.actions:
                out.extend(a.name for a in t.actions.actions)
        return out

    def _all_event_names(self) -> list[str]:
        return [t.event.name for t in self.s.plan.transitions if t.event is not None]

    def _strategic_rules(self) -> None:
        pattern = self.s.intent.pattern if self.s.intent else None
        if not pattern:
            return

        actions = self._all_action_names()
        events = self._all_event_names()

        if pattern == "Feint":
            if "retarget" not in actions and "move" not in actions:
                self.d.warn(
                    "C001_FEINT_NO_REDEPLOY",
                    "Feint should include an induced enemy relocation/retarget response",
                )
            if actions.count("attack") < 1:
                self.d.warn(
                    "C002_FEINT_NO_EXPLOIT",
                    "Feint should culminate in an attack/exploit against the real objective",
                )

        elif pattern == "Trap":
            if not any(a in actions for a in {"block", "set_mode"}):
                self.d.warn(
                    "C010_TRAP_NO_CLOSURE",
                    "Trap should contain an explicit closure/mobility-denial action",
                )
            if not any(e in events for e in {"enter", "unit_attacked"}):
                self.d.warn(
                    "C011_TRAP_NO_COMMIT",
                    "Trap should observe enemy commitment before closure",
                )

        elif pattern == "IndirectRelief":
            if "retarget" not in actions:
                self.d.warn(
                    "C020_RELIEF_NO_RETARGET",
                    "IndirectRelief should causally force enemy retargeting/relocation",
                )
            if "attack" not in actions:
                self.d.warn(
                    "C021_RELIEF_NO_EXPLOIT",
                    "IndirectRelief should include interception or exploitation after relief",
                )

        elif pattern == "SacrificeBait":
            if "unit_died" not in events and "killed_in" not in self._collect_call_names(self.s.intent.primary):
                self.d.warn(
                    "C030_SACRIFICE_NO_LOSS_TRIGGER",
                    "SacrificeBait should explicitly observe bounded bait losses",
                )
            if not any(a in actions for a in {"set_mode", "retarget", "retreat", "attack"}):
                self.d.warn(
                    "C031_SACRIFICE_NO_COMPENSATION",
                    "SacrificeBait needs a compensating enemy mode/position change or exploit",
                )

        elif pattern == "BorrowedWeapon":
            if "control" not in actions:
                self.d.warn(
                    "C040_BORROW_NO_CONTROL",
                    "BorrowedWeapon requires a control/capability-capture action",
                )
            if "attack" not in actions:
                self.d.warn(
                    "C041_BORROW_NO_REDIRECT",
                    "BorrowedWeapon should redirect captured power against another target",
                )


    def _pattern_causal_rules(self) -> None:
        report = PatternChecker(self.s, self.symbol_types).check()
        self.pattern_report = report
        self.d.extend(report.diagnostics)

    def _collect_call_names(self, e: Expr) -> set[str]:
        out: set[str] = set()

        def walk(x: Expr):
            if isinstance(x, CallExpr):
                out.add(x.name)
                for a in x.args:
                    walk(a)
            elif isinstance(x, UnaryExpr):
                walk(x.operand)
            elif isinstance(x, BinaryExpr):
                walk(x.left)
                walk(x.right)

        walk(e)
        return out
