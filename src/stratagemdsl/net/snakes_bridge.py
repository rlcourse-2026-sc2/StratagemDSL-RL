"""Cross-check the token rules against SNAKES (LGPL, https://snakes.ibisc.univ-evry.fr).

SNAKES is an independent Python Petri-net library. `cross_check(net)`
expands the Strategic Petri Net to its plain P/T skeleton
(`pnml.expand_plain`), builds the same net in SNAKES with black tokens --
weights as MultiArc, read arcs as Test, inhibitor arcs as Inhibitor -- and
compares SNAKES' state graph with `pnml.plain_reachability`. Agreement means
our enabling and firing rules (weights, read, inhibitor, capacity and `once`
encodings, halting) match a reference implementation.

SNAKES is an optional dependency (`pip install snakes`).
"""
from __future__ import annotations

from dataclasses import dataclass

from stratagemdsl.net.model import PetriNet
from stratagemdsl.net.pnml import expand_plain, plain_reachability


@dataclass
class CrossCheck:
    ok: bool
    ours: int
    snakes: int
    only_ours: list
    only_snakes: list
    skipped: str = ""


def to_snakes(plain: PetriNet):
    from snakes.nets import Inhibitor, MultiArc, PetriNet as SNet, Place, Test, Transition, Value, dot
    n = SNet(plain.name)
    for p in plain.places.values():
        n.add_place(Place(p.id, [dot] * p.initial))

    def annotation(w):
        return Value(dot) if w == 1 else MultiArc([Value(dot)] * w)

    for t in plain.transitions:
        if t.guard_static is False:
            continue
        n.add_transition(Transition(t.id))
        for a in t.inputs:
            ann = annotation(a.weight)
            if a.kind == "read":
                ann = Test(ann)
            elif a.kind == "inhibit":
                ann = Inhibitor(ann)
            n.add_input(a.place, t.id, ann)
        for a in t.outputs:
            n.add_output(a.place, t.id, annotation(a.weight))
    return n


def snakes_reachability(plain: PetriNet, limit: int = 200_000):
    from snakes.nets import StateGraph
    g = StateGraph(to_snakes(plain))
    out = set()
    for state in g:
        if state >= limit:
            break
        g.goto(state)
        out.add(tuple(sorted((p.name, len(p.tokens)) for p in g.net.place() if len(p.tokens))))
    return out


def cross_check(net: PetriNet, limit: int = 20_000) -> CrossCheck:
    plain = expand_plain(net)
    ours = {tuple(sorted(m)) for m in plain_reachability(plain, limit)}
    if len(ours) >= limit:
        # An unbounded (or huge) skeleton: N001 reports it; both explorations
        # would be truncated at different frontiers, so there is nothing to compare.
        return CrossCheck(True, len(ours), 0, [], [], skipped=f"more than {limit} plain markings")
    theirs = snakes_reachability(plain)
    return CrossCheck(ours == theirs, len(ours), len(theirs),
                      sorted(ours - theirs)[:5], sorted(theirs - ours)[:5])
