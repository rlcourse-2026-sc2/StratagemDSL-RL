"""Compile a Strategy's plan into a Strategic Petri Net.

Desugaring rules (each is checked by tests/l3_net):

  phase P                 place P, capacity 1, `once` unless `repeatable`
  place Q {initial n; capacity c}
                          resource place Q with n initial tokens
  start [P, ...]          one initial token in each listed phase
  join J all              per incoming edge e: place J.in.e (capacity 1, once)
                          silent immediate transition J.sync:
                              J.in.e1, ..., J.in.ek -> J
  join J any / atleast(k) place J.arrivals (capacity = indegree)
                          place J.armed (1 initial token): the join fires once
                          silent immediate transition J.sync:
                              J.arrivals*k, J.armed -> J        (any: k = 1)
  transition t: ins -> outs
                          net transition t; an output arc to a join is
                          redirected to that join's input/arrival place
  terminal_policy first_wins
                          the net halts on the first marked terminal place

Dispatch classes (see stratagemdsl.net.model):

  event      the transition has `on ...`
  immediate  no event and a constant-true guard (or a guard that reads only
             the marking), unless a conflicting eventless transition with a
             live guard has higher priority -- then it is `polled` and acts as
             the priority-ordered fallback of that poll (v0.2 rule R03)
  polled     no event and a live guard
"""
from __future__ import annotations

from collections import defaultdict
from typing import Optional

from stratagemdsl.core.ast_utils import binding_named
from stratagemdsl.core.model import (
    BindingCall, BoolExpr, CallExpr, Join, NameExpr, NumberExpr, Phase, Place, StringExpr, Strategy,
)
from stratagemdsl.net.guards import is_marking_only, static_truth
from stratagemdsl.net.model import (
    EVENT, IMMEDIATE, POLLED, NetArc, NetPlace, NetTransition, PetriNet,
)

SILENT_PRIORITY = -1


def event_signature(event: CallExpr) -> tuple:
    """Key identifying 'the same observable event' (same name and arguments)."""
    def arg_key(a):
        if isinstance(a, NameExpr):
            return ("name", a.name)
        if isinstance(a, StringExpr):
            return ("str", a.value)
        if isinstance(a, (NumberExpr, BoolExpr)):
            return ("lit", a.value)
        return ("other", repr(a))
    return (event.name, tuple(arg_key(a) for a in event.args))


def terminal_policy(strategy: Strategy) -> str:
    setup = next((b.value for b in strategy.bindings if b.name == "__setup__"), None)
    if isinstance(setup, BindingCall):
        return str(binding_named(setup, "terminal_policy", "legacy"))
    return "legacy"


def join_place_ids(join_id: str) -> dict[str, str]:
    return {"arrivals": f"{join_id}.arrivals", "armed": f"{join_id}.armed", "sync": f"{join_id}.sync"}


def build_net(strategy: Strategy) -> PetriNet:
    plan = strategy.plan
    net = PetriNet(name=strategy.name, halting=terminal_policy(strategy) == "first_wins",
                   derived={d.name: d.expr for d in strategy.derived})
    if plan is None:
        return net
    nodes = {}
    for n in plan.nodes:
        nodes.setdefault(n.id, n)
    starts = set(plan.start or [])

    # ---------------------------------------------------------------- places
    for n in plan.nodes:
        if n.id in net.places:
            continue
        if isinstance(n, Phase):
            net.places[n.id] = NetPlace(
                n.id, "phase", n.id, initial=1 if n.id in starts else 0, capacity=1,
                once=not n.repeatable, terminal=n.terminal, label=n.purpose)
        elif isinstance(n, Join):
            net.places[n.id] = NetPlace(n.id, "join", n.id, capacity=1, once=True,
                                        label=f"join {n.policy}" + (f"({n.quorum})" if n.policy == "atleast" else ""))
        elif isinstance(n, Place):
            net.places[n.id] = NetPlace(n.id, "resource", n.id, initial=int(n.tokens or 0),
                                        capacity=n.capacity, label=n.purpose)

    # ------------------------------------------------- join synchronisation
    incoming: dict[str, list] = defaultdict(list)
    for t in plan.transitions:
        for a in t.outputs:
            if isinstance(nodes.get(a.place), Join):
                incoming[a.place].append(t)
    redirect: dict[tuple[str, str], str] = {}   # (transition id, join id) -> input place
    silent: list[NetTransition] = []
    for n in plan.nodes:
        if not isinstance(n, Join) or n.id not in net.places:
            continue
        edges = incoming.get(n.id, [])
        ids = join_place_ids(n.id)
        if n.policy == "all":
            ins = []
            for e in edges:
                pid = f"{n.id}.in.{e.id}"
                if pid in net.places:
                    continue
                net.places[pid] = NetPlace(pid, "join_input", n.id, capacity=1, once=True,
                                           label=f"{e.id} arrived at {n.id}")
                redirect[(e.id, n.id)] = pid
                ins.append(NetArc(pid))
            if not ins:
                continue
            silent.append(NetTransition(ids["sync"], None, IMMEDIATE, ins, [NetArc(n.id)],
                                        SILENT_PRIORITY, 0, silent=True, trigger=("immediate",),
                                        guard_static=True, note=f"join {n.id} all"))
        else:
            need = 1 if n.policy == "any" else max(1, int(n.quorum or 1))
            arr = ids["arrivals"]
            net.places[arr] = NetPlace(arr, "join_arrivals", n.id, capacity=max(1, len(edges)),
                                       label=f"arrivals at {n.id}")
            net.places[ids["armed"]] = NetPlace(ids["armed"], "join_armed", n.id, initial=1, capacity=1,
                                                label=f"{n.id} not yet released")
            for e in edges:
                redirect[(e.id, n.id)] = arr
            silent.append(NetTransition(ids["sync"], None, IMMEDIATE, [NetArc(arr, need), NetArc(ids["armed"])],
                                        [NetArc(n.id)], SILENT_PRIORITY, 0, silent=True,
                                        trigger=("immediate",), guard_static=True,
                                        note=f"join {n.id} {n.policy}" + (f"({need})" if n.policy == "atleast" else "")))

    # ------------------------------------------------------- transitions
    for order, t in enumerate(plan.transitions, start=1):
        if any(x.origin == t.id for x in net.transitions):
            continue   # duplicate id; the validator reports P005
        ins = [NetArc(a.place, int(a.weight), a.kind) for a in t.inputs if a.place in net.places]
        outs = []
        for a in t.outputs:
            target = redirect.get((t.id, a.place), a.place)
            if target in net.places:
                outs.append(NetArc(target, int(a.weight)))
        st = static_truth(t.guard)
        marking_guard = t.guard is not None and st is None and is_marking_only(t.guard, net.derived)
        if t.event is not None:
            dispatch, trigger = EVENT, ("event", event_signature(t.event))
        elif st is True or marking_guard:
            dispatch, trigger = IMMEDIATE, ("immediate",)
        else:
            dispatch, trigger = POLLED, ("poll",)
        net.transitions.append(NetTransition(
            t.id, t.id, dispatch, ins, outs, int(t.priority), order, event=t.event, guard=t.guard,
            actions=t.actions, trigger=trigger, guard_static=st, marking_guard=marking_guard))

    # Demotion (v0.2 R03): an eventless transition that is not live-guarded
    # may only fire eagerly when no conflicting live-guarded eventless
    # transition outranks it; otherwise it is that poll's fallback branch.
    changed = True
    while changed:
        changed = False
        for t in net.transitions:
            if t.dispatch != IMMEDIATE:
                continue
            for u in net.transitions:
                if (u.dispatch == POLLED and net.in_conflict(t, u) and u.priority < t.priority):
                    t.dispatch, t.trigger = POLLED, ("poll",)
                    t.note = f"fallback of the poll led by '{u.id}'"
                    changed = True
                    break

    for i, s in enumerate(silent):
        s.order = len(plan.transitions) + 1 + i
    net.transitions.extend(silent)
    if net.halting:
        net.notes.append("first_wins: the first marked terminal place halts the net")
    return net


def node_of(net: PetriNet, place_id: str) -> Optional[str]:
    p = net.places.get(place_id)
    return p.origin if p else None
