from __future__ import annotations

from dataclasses import dataclass, field
from collections import defaultdict, deque
from typing import Iterable, Optional

from stratagemdsl.core.model import Strategy, Phase, Transition, CallExpr, NameExpr, StringExpr, NumberExpr, BoolExpr, Expr
from stratagemdsl.semantics.patterns.library import FactPattern, InterpretationRule, get_pattern


# Fact kinds produced directly from plan actions and events (_action_fact,
# _event_fact). Pattern rules derive the others.
ACTION_FACT_KINDS = frozenset({"Attack", "Relocate", "Control", "Block", "Conceal", "SetMode"})
EVENT_FACT_KINDS = frozenset({"Enter", "Leave", "UnitDied", "UnitAttacked", "AbilityCast",
                              "AbilityCompleted", "ConstructionCompleted"})


@dataclass(frozen=True)
class StrategicFact:
    id: str
    kind: str
    args: tuple[str, ...]
    origin_kind: str  # phase | transition | derived
    origin_id: str
    evidence: str

    def short(self) -> str:
        return f"{self.kind}({', '.join(self.args)}) @ {self.origin_kind}:{self.origin_id}"


@dataclass(frozen=True)
class CausalEdge:
    source: str
    target: str
    evidence: str
    strength: str = "strong"


@dataclass
class StrategicFactGraph:
    facts: list[StrategicFact] = field(default_factory=list)
    edges: list[CausalEdge] = field(default_factory=list)

    def __post_init__(self) -> None:
        self._by_id = {f.id: f for f in self.facts}
        self._adj: dict[str, list[CausalEdge]] = defaultdict(list)
        for e in self.edges:
            self._adj[e.source].append(e)

    def matching(self, kind: str, args: tuple[str, ...]) -> list[StrategicFact]:
        return [f for f in self.facts if f.kind == kind and f.args == args]

    def find_path(self, source: StrategicFact, target: StrategicFact) -> Optional[list[StrategicFact]]:
        if source.id == target.id:
            return [source]
        q = deque([source.id])
        prev: dict[str, Optional[str]] = {source.id: None}
        while q:
            u = q.popleft()
            for e in self._adj.get(u, []):
                v = e.target
                if v in prev:
                    continue
                prev[v] = u
                if v == target.id:
                    ids = [v]
                    cur = u
                    while cur is not None:
                        ids.append(cur)
                        cur = prev[cur]
                    ids.reverse()
                    return [self._by_id[x] for x in ids]
                q.append(v)
        return None


class FactExtractor:
    """Extracts a small strategic fact graph from a concrete Strategy.

    Concrete events/actions are extracted first.  The declared pattern's
    interpretation rules (`PatternDef.interpretations` in the library) then add
    the strategic facts its obligations talk about, such as Threat or
    DefenseWeakened.  This is intentionally above the Galaxy backend: the
    backend remains concerned only with executable primitives.
    """

    def __init__(self, s: Strategy) -> None:
        self.s = s
        self.facts: list[StrategicFact] = []
        self.edges: list[CausalEdge] = []
        self._counter = 0

    def _add(self, kind: str, args: Iterable[str], origin_kind: str, origin_id: str, evidence: str) -> StrategicFact:
        self._counter += 1
        f = StrategicFact(
            id=f"F{self._counter:04d}",
            kind=kind,
            args=tuple(args),
            origin_kind=origin_kind,
            origin_id=origin_id,
            evidence=evidence,
        )
        self.facts.append(f)
        return f

    def _name(self, e: Expr) -> Optional[str]:
        return e.name if isinstance(e, NameExpr) else None

    def _value(self, e: Expr) -> Optional[str]:
        if isinstance(e, NameExpr):
            return e.name
        if isinstance(e, StringExpr):
            return e.value
        if isinstance(e, (NumberExpr, BoolExpr)):
            return str(e.value)
        return None

    def _calls(self, block) -> list[CallExpr]:
        return list(block.actions) if block is not None else []

    def extract(self) -> StrategicFactGraph:
        trans_by_source: dict[str, list[Transition]] = defaultdict(list)
        for t in self.s.plan.transitions:
            trans_by_source[t.source].append(t)

        origin_facts: dict[tuple[str, str], list[StrategicFact]] = defaultdict(list)

        # Phase actions -> primitive strategic facts.
        for n in self.s.plan.nodes:
            if not isinstance(n, Phase):
                continue
            phase_facts: list[StrategicFact] = []
            for a in self._calls(n.actions):
                fact = self._action_fact(a, "phase", n.id)
                if fact:
                    origin_facts[("phase", n.id)].append(fact)
                    phase_facts.append(fact)
            if n.actions is not None and n.actions.mode == "sequence":
                for left, right in zip(phase_facts, phase_facts[1:]):
                    self.edges.append(CausalEdge(left.id, right.id, "sequential action order", "strong"))

            self._interpret("phase", n.id, phase_facts, None, origin_facts)

        # Transition event/action facts and direct event-response relations.
        for t in self.s.plan.transitions:
            event_fact = self._event_fact(t.event, t.id) if t.event else None
            if event_fact:
                origin_facts[("transition", t.id)].append(event_fact)
            action_facts: list[StrategicFact] = []
            for a in self._calls(t.actions):
                fact = self._action_fact(a, "transition", t.id)
                if fact:
                    action_facts.append(fact)
                    origin_facts[("transition", t.id)].append(fact)
                    if event_fact:
                        self.edges.append(CausalEdge(event_fact.id, fact.id, "same-transition event -> response", "strong"))
            if t.actions is not None and t.actions.mode == "sequence":
                for left, right in zip(action_facts, action_facts[1:]):
                    self.edges.append(CausalEdge(left.id, right.id, "sequential action order", "strong"))

            self._interpret("transition", t.id, action_facts, event_fact, origin_facts)

        # Derived facts: retain dependency markers useful for witnesses/debugging.
        for d in self.s.derived:
            f = self._add("Derived", (d.name,), "derived", d.name, "scenario-local derived fact")
            origin_facts[("derived", d.name)].append(f)

        # Control-flow ordering connects facts across PlanGraph origins. We only
        # connect forward-reachable origins; this makes obligation paths respect
        # actual strategic ordering rather than bag-of-actions occurrence.
        origin_adj: dict[tuple[str, str], set[tuple[str, str]]] = defaultdict(set)
        for t in self.s.plan.transitions:
            # v0.6 arcs: every consumed or read place precedes the transition,
            # every output place follows it.
            for a in t.inputs:
                if a.kind != "inhibit":
                    origin_adj[("phase", a.place)].add(("transition", t.id))
            for a in t.outputs:
                origin_adj[("transition", t.id)].add(("phase", a.place))
            # Join nodes may sit between transitions; model them as phase-like
            # origin names even though they carry no facts themselves.

        # Phase->transition edges for all outgoing transitions naturally handle joins.
        # For facts at each origin, connect to facts at any later reachable origin.
        reach_cache: dict[tuple[str, str], set[tuple[str, str]]] = {}

        def reachable(o):
            if o in reach_cache:
                return reach_cache[o]
            seen = set()
            q = deque(origin_adj.get(o, set()))
            while q:
                x = q.popleft()
                if x in seen:
                    continue
                seen.add(x)
                q.extend(origin_adj.get(x, set()))
            reach_cache[o] = seen
            return seen

        for o1, fs1 in origin_facts.items():
            later = reachable(o1)
            for o2 in later:
                for a in fs1:
                    for b in origin_facts.get(o2, []):
                        self.edges.append(CausalEdge(a.id, b.id, "PlanGraph control-flow precedence", "ordering"))

        return StrategicFactGraph(self.facts, self.edges)

    # ------------------------------------------------ interpretation rules
    def _rules(self, scope: str) -> list[InterpretationRule]:
        intent = self.s.intent
        if intent is None or not intent.pattern_bindings:
            return []
        p = get_pattern(intent.pattern)
        return [r for r in p.interpretations if r.scope in (scope, "any")] if p else []

    @staticmethod
    def _matches(fp: FactPattern, fact: Optional[StrategicFact], pb: dict[str, str]) -> bool:
        if fact is None or fact.kind != fp.kind or len(fact.args) < len(fp.args):
            return False
        for want, got in zip(fp.args, fact.args):
            if want == "_":
                continue
            if want.startswith("$"):
                if pb.get(want[1:]) != got:
                    return False
            elif want != got:
                return False
        return True

    @staticmethod
    def _roles(rule: InterpretationRule) -> set[str]:
        pats = [fp for _, fp in rule.match] + ([rule.event] if rule.event else []) + [d.fact for d in rule.derive]
        roles = {a[1:] for fp in pats for a in fp.args if a.startswith("$")}
        return roles | {r for pair in rule.distinct for r in pair}

    def _interpret(self, scope: str, origin_id: str, own: list[StrategicFact],
                   event_fact: Optional[StrategicFact], origin_facts) -> None:
        """Fire the declared pattern's rules on one phase or transition."""
        rules = self._rules(scope)
        if not rules:
            return
        pb = self.s.intent.pattern_bindings
        live = [r for r in rules
                if all(pb.get(x) is not None for x in self._roles(r))
                and all(pb[a] != pb[b] for a, b in r.distinct)
                and (r.event is None or self._matches(r.event, event_fact, pb))]

        def fire(rule: InterpretationRule, anchor: Optional[StrategicFact]) -> None:
            bound = {"event": event_fact}
            for i, (label, fp) in enumerate(rule.match):
                hit = anchor if i == 0 else next((f for f in own if self._matches(fp, f, pb)), None)
                if hit is None:
                    return
                bound[label] = hit
            for d in rule.derive:
                args = tuple(pb[a[1:]] if a.startswith("$") else a for a in d.fact.args)
                new = self._add(d.fact.kind, args, scope, origin_id, d.evidence)
                origin_facts[(scope, origin_id)].append(new)
                ends = dict(bound, new=new)
                for link in d.links:
                    self.edges.append(CausalEdge(ends[link.source].id, ends[link.target].id, link.evidence, link.strength))

        # Anchored rules fire per matching fact, in fact order and then rule order.
        for f in list(own):
            for rule in live:
                if rule.match and self._matches(rule.match[0][1], f, pb):
                    fire(rule, f)
        for rule in live:
            if not rule.match and event_fact is not None:
                fire(rule, None)

    def _action_fact(self, a: CallExpr, origin_kind: str, origin_id: str) -> Optional[StrategicFact]:
        names = tuple(self._value(x) for x in a.args)
        if any(x is None for x in names):
            return None
        if a.name == "attack" and len(names) >= 2:
            return self._add("Attack", names[:2], origin_kind, origin_id, "attack action")
        if a.name in {"retarget", "move", "retreat"} and len(names) >= 2:
            return self._add("Relocate", names[:2], origin_kind, origin_id, f"{a.name} action")
        if a.name == "control" and len(names) >= 2:
            return self._add("Control", names[:2], origin_kind, origin_id, "control action")
        if a.name == "block" and len(names) >= 2:
            return self._add("Block", names[:2], origin_kind, origin_id, "block action")
        if a.name == "set_mode" and len(names) >= 2:
            return self._add("SetMode", names[:2], origin_kind, origin_id, "set_mode action")
        if a.name == "cast" and len(names) >= 2 and names[1].lower() in {"burrow", "cloak", "sneak"}:
            return self._add("Conceal", names[:1], origin_kind, origin_id, f"{names[1]} concealment action")
        return None

    def _event_fact(self, e: CallExpr, transition_id: str) -> Optional[StrategicFact]:
        # String arguments count too: ability_completed(gate, "SupplyDepotRaise").
        names = tuple(self._value(x) for x in e.args)
        if any(x is None for x in names):
            return None
        mapping = {
            "enter": "Enter",
            "leave": "Leave",
            "unit_died": "UnitDied",
            "unit_attacked": "UnitAttacked",
            "ability_cast": "AbilityCast",
            "ability_completed": "AbilityCompleted",
            "construction_completed": "ConstructionCompleted",
        }
        kind = mapping.get(e.name)
        if not kind:
            return None
        return self._add(kind, names, "transition", transition_id, f"{e.name} event")
