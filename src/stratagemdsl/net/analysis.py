"""State-space analysis of a Strategic Petri Net.

The net is split into independent components (no shared place, no marking
guard reading another component); each component's abstract reachability
graph is explored breadth first with the step semantics of
`net.semantics.TokenGame`, treating every world guard as a free boolean.
That over-approximates the runs the game can produce, so

  * "never fires" / "never marked" / "join can never complete" are proofs,
  * "can get stuck" / "can overflow" are possibilities (witness included).

Cross-component halting (first_wins) only removes behaviour, so ignoring it
keeps the over-approximation sound.
"""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from typing import Optional

from stratagemdsl.net.guards import marking_refs
from stratagemdsl.net.model import IMMEDIATE, NetPlace, NetTransition, PetriNet
from stratagemdsl.net.semantics import State, TokenGame, ZenoError

STATE_LIMIT = 50_000
UNBOUNDED_CUTOFF = 64     # a capacity-less place above this is reported unbounded


@dataclass
class ComponentResult:
    places: list[str]
    transitions: list[str]
    states: int = 0
    edges: int = 0
    complete: bool = True
    truncated_choices: bool = False
    fired: set[str] = field(default_factory=set)
    marked: set[str] = field(default_factory=set)
    bound: dict[str, int] = field(default_factory=dict)
    blocked: dict[str, list[str]] = field(default_factory=dict)   # transition -> witness
    stuck: Optional[dict] = None                                  # {"marking":..., "trace":[...]}
    terminals: dict[str, list[str]] = field(default_factory=dict) # terminal -> witness trace
    unbounded: dict[str, list[str]] = field(default_factory=dict)
    zeno: Optional[str] = None
    # transition -> dispatch sequence [(trigger, transition ids whose guard is true)]
    # that fires it from the initial marking (used to drive differential tests)
    witness: dict[str, list[tuple[tuple, tuple]]] = field(default_factory=dict)


@dataclass
class NetReport:
    net: PetriNet
    components: list[ComponentResult]
    immediate_cycles: list[list[str]]

    # --------------------------------------------------------- aggregates
    @property
    def complete(self) -> bool:
        return all(c.complete for c in self.components)

    @property
    def states(self) -> int:
        n = 1
        for c in self.components:
            n *= max(1, c.states)
        return n

    def fired(self) -> set[str]:
        return set().union(*(c.fired for c in self.components)) if self.components else set()

    def marked(self) -> set[str]:
        return set().union(*(c.marked for c in self.components)) if self.components else set()

    def bound(self) -> dict[str, int]:
        out: dict[str, int] = {}
        for c in self.components:
            out.update(c.bound)
        return out

    def dead_transitions(self) -> list[NetTransition]:
        fired = self.fired()
        return [t for t in self.net.transitions if t.id not in fired]

    def never_marked(self) -> list[NetPlace]:
        marked = self.marked()
        return [p for p in self.net.places.values() if p.id not in marked]

    def global_stuck(self) -> Optional[list[dict]]:
        """Every component can be stuck at once without any terminal result."""
        if not self.components:
            return None
        if any(c.stuck is None for c in self.components):
            return None
        return [c.stuck for c in self.components]

    def witnesses(self) -> dict[str, list[tuple[tuple, tuple]]]:
        out: dict[str, list] = {}
        for c in self.components:
            out.update(c.witness)
        return out

    def terminal_reached(self) -> dict[str, list[str]]:
        out: dict[str, list[str]] = {}
        for c in self.components:
            out.update(c.terminals)
        return out

    def summary(self) -> dict:
        return {
            "net": self.net.stats(),
            "components": len(self.components),
            "states": self.states,
            "complete": self.complete,
            "dead_transitions": [t.id for t in self.dead_transitions()],
            "never_marked": [p.id for p in self.never_marked()],
            "bounds": self.bound(),
            "terminals_reachable": sorted(self.terminal_reached()),
            "global_stuck": self.global_stuck(),
            "immediate_cycles": self.immediate_cycles,
            "unbounded": sorted(set().union(*(set(c.unbounded) for c in self.components))) if self.components else [],
            "capacity_blocked": sorted(set().union(*(set(c.blocked) for c in self.components))) if self.components else [],
        }


# ------------------------------------------------------------- structure
def components(net: PetriNet) -> list[tuple[list[str], list[str]]]:
    parent = {p: p for p in net.places}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb

    for t in net.transitions:
        ps = [a.place for a in t.inputs + t.outputs]
        ps += [p for p in marking_refs(t.guard, net.derived) if p in net.places]
        for a, b in zip(ps, ps[1:]):
            union(a, b)
    groups: dict[str, list[str]] = {}
    for p in net.places:
        groups.setdefault(find(p), []).append(p)
    out = []
    for places in groups.values():
        pset = set(places)
        trans = [t.id for t in net.transitions
                 if any(a.place in pset for a in t.inputs + t.outputs)]
        out.append((places, trans))
    return out


def immediate_cycles(net: PetriNet) -> list[list[str]]:
    """Cycles made only of immediate transitions (a settle could never end)."""
    graph: dict[str, set[str]] = {}
    for t in net.transitions:
        if t.dispatch != IMMEDIATE or t.guard_static is False:
            continue
        for a in t.inputs:
            if a.kind != "normal":
                continue
            for b in t.outputs:
                graph.setdefault(a.place, set()).add(b.place)
    cycles, color, stack = [], {}, []

    def dfs(u):
        color[u] = 1
        stack.append(u)
        for v in sorted(graph.get(u, ())):
            if color.get(v, 0) == 0:
                dfs(v)
            elif color.get(v) == 1:
                cycles.append(stack[stack.index(v):] + [v])
        stack.pop()
        color[u] = 2

    for u in sorted(graph):
        if color.get(u, 0) == 0:
            dfs(u)
    return cycles


def subnet(net: PetriNet, places: list[str], transitions: list[str]) -> PetriNet:
    keep = set(transitions)
    return PetriNet(net.name, {p: net.places[p] for p in places},
                    [t for t in net.transitions if t.id in keep], net.halting, net.derived)


# ------------------------------------------------------------ exploration
def _explore(net: PetriNet, places: list[str], trans: list[str], limit: int) -> ComponentResult:
    sub = subnet(net, places, trans)
    res = ComponentResult(places, trans)
    game = TokenGame(sub)
    try:
        init = game.initial()
    except ZenoError as e:
        res.zeno = str(e)
        res.complete = False
        return res
    parent: dict[State, tuple[Optional[State], tuple, Optional[tuple]]] = {init: (None, (), None)}
    queue = deque([init])

    def trace(s: State) -> list[str]:
        out: list[str] = []
        while s is not None:
            prev, fired, _step = parent[s]
            out[0:0] = list(fired)
            s = prev
        return out

    def steps_to(s: State) -> list[tuple[tuple, tuple]]:
        out = []
        while s is not None:
            prev, _fired, step = parent[s]
            if step is not None:
                out.insert(0, step)
            s = prev
        return out

    def visit(s: State) -> None:
        for i, n in enumerate(s.marking):
            if n:
                pid = game.places[i].id
                res.marked.add(pid)
                if n > res.bound.get(pid, 0):
                    res.bound[pid] = n
                p = game.places[i]
                if p.terminal and pid not in res.terminals:
                    res.terminals[pid] = trace(s)
                if p.capacity is None and n > UNBOUNDED_CUTOFF and pid not in res.unbounded:
                    res.unbounded[pid] = trace(s)
            else:
                res.bound.setdefault(game.places[i].id, 0)

    visit(init)
    # Settling the initial marking already fired immediate transitions.
    first = _initial_log(game)
    res.fired |= set(first.fired)
    res.witness.update({tid: [] for tid in first.fired})
    res.marked |= set(first.entered)
    while queue:
        s = queue.popleft()
        if game.stuck(s) and res.stuck is None and not any(
                game.places[i].terminal for i, n in enumerate(s.marking) if n):
            res.stuck = {"marking": game.marked(s), "trace": trace(s)}
        for x in game.ts.values():
            if x.id not in res.blocked and game.capacity_blocked(s, x):
                res.blocked[x.id] = trace(s)
        if any(n > UNBOUNDED_CUTOFF for i, n in enumerate(s.marking) if game.cap[i] is None):
            continue
        try:
            succ, truncated = game.successors(s)
        except ZenoError as e:
            res.zeno = str(e)
            res.complete = False
            continue
        res.truncated_choices |= truncated
        for trigger, fired, nxt, log, selected in succ:
            res.edges += 1
            for tid in fired:
                if tid not in res.witness:
                    res.witness[tid] = steps_to(s) + [(trigger, selected)]
            res.fired.update(fired)
            res.marked.update(log.entered)
            if nxt in parent:
                continue
            if len(parent) >= limit:
                res.complete = False
                continue
            parent[nxt] = (s, fired, (trigger, selected))
            visit(nxt)
            queue.append(nxt)
    res.states = len(parent)
    return res


def _initial_log(game: TokenGame):
    from stratagemdsl.net.semantics import StepLog
    log = StepLog()
    try:
        game.initial(log)
    except ZenoError:
        return StepLog()
    return log


def analyze(net: PetriNet, *, limit: int = STATE_LIMIT) -> NetReport:
    comps = [_explore(net, ps, ts, limit) for ps, ts in components(net)]
    return NetReport(net, comps, immediate_cycles(net))
