"""PNML interchange and the plain P/T expansion of a Strategic Petri Net.

`to_pnml(net)` writes ISO/IEC 15909-2 PNML (P/T net type). Read arcs and
inhibitor arcs use the common `<type value="test|inhibitor"/>` arc extension
(PIPE, TAPAAL, GreatSPN); dispatch class, priority, guard and the `once` /
capacity attributes travel in a `<toolspecific tool="StratagemDSL">` block,
so tools that ignore it still see a faithful net *structure*.

`expand_plain(net)` removes the two non-standard place rules so external
P/T tools explore the same token rules:

  capacity c on p   complement place p~ with c - m0(p) tokens; a transition
                    whose net effect on p is +d consumes d from p~, -d refills it
  once p            complement place p^ (1 token while p was never entered);
                    each transition producing into p splits into a "fresh"
                    variant (consumes p^, produces p) and a "stale" variant
                    (inhibited by p^, drops the token)
  halting           place halt; every transition is inhibited by it and
                    every arc into a terminal also produces into it (the
                    clearing of other places is not expressible without
                    reset arcs; the halted net simply stops)

Guards, priorities and maximal progress are deliberately *not* expanded: the
plain net is the untimed, guard-free skeleton (every guard may be true).
"""
from __future__ import annotations

from itertools import product
from xml.etree import ElementTree as ET

from stratagemdsl.frontend.unparse import _print_expr
from stratagemdsl.net.model import IMMEDIATE, NetArc, NetPlace, NetTransition, PetriNet

PTNET = "http://www.pnml.org/version-2009/grammar/ptnet"


def _sid(x: str) -> str:
    return "".join(c if c.isalnum() or c in "_-" else "_" for c in x)


def to_pnml(net: PetriNet, *, plain: bool = False) -> str:
    if plain:
        net = expand_plain(net)
    root = ET.Element("pnml", xmlns="http://www.pnml.org/version-2009/grammar/pnml")
    n = ET.SubElement(root, "net", id=_sid(net.name), type=PTNET)
    ET.SubElement(ET.SubElement(n, "name"), "text").text = net.name
    page = ET.SubElement(n, "page", id="plan")
    for p in net.places.values():
        el = ET.SubElement(page, "place", id="p_" + _sid(p.id))
        ET.SubElement(ET.SubElement(el, "name"), "text").text = p.id
        if p.initial:
            ET.SubElement(ET.SubElement(el, "initialMarking"), "text").text = str(p.initial)
        ts = ET.SubElement(el, "toolspecific", tool="StratagemDSL", version="0.6")
        ET.SubElement(ts, "place", kind=p.kind, origin=p.origin, once=str(p.once).lower(),
                      capacity="" if p.capacity is None else str(p.capacity), terminal=p.terminal or "")
    arc_no = 0
    for t in net.transitions:
        el = ET.SubElement(page, "transition", id="t_" + _sid(t.id))
        ET.SubElement(ET.SubElement(el, "name"), "text").text = t.id
        ts = ET.SubElement(el, "toolspecific", tool="StratagemDSL", version="0.6")
        attrs = {"dispatch": t.dispatch, "priority": str(t.priority), "order": str(t.order),
                 "silent": str(t.silent).lower()}
        if t.event is not None:
            attrs["event"] = _print_expr(t.event)
        if t.guard is not None:
            attrs["guard"] = _print_expr(t.guard)
        ET.SubElement(ts, "transition", **attrs)
        for a in t.inputs:
            arc_no += 1
            arc = ET.SubElement(page, "arc", id=f"a{arc_no}", source="p_" + _sid(a.place), target="t_" + _sid(t.id))
            if a.weight != 1:
                ET.SubElement(ET.SubElement(arc, "inscription"), "text").text = str(a.weight)
            if a.kind != "normal":
                ET.SubElement(arc, "type", value="test" if a.kind == "read" else "inhibitor")
        for a in t.outputs:
            arc_no += 1
            arc = ET.SubElement(page, "arc", id=f"a{arc_no}", source="t_" + _sid(t.id), target="p_" + _sid(a.place))
            if a.weight != 1:
                ET.SubElement(ET.SubElement(arc, "inscription"), "text").text = str(a.weight)
    ET.indent(root)
    return '<?xml version="1.0" encoding="utf-8"?>\n' + ET.tostring(root, encoding="unicode") + "\n"


def from_pnml(text: str) -> dict:
    """Structure of a PNML document: {places: {id: m0}, transitions: [...], arcs: [...]}.

    Enough to round-trip what `to_pnml` writes (used by tests and tools)."""
    root = ET.fromstring(text)
    ns = {"p": "http://www.pnml.org/version-2009/grammar/pnml"}
    places, transitions, arcs = {}, [], []
    names = {}
    for el in root.iter():
        tag = el.tag.split("}")[-1]
        if tag in ("place", "transition") and el.get("id"):
            name_el = next((c for c in el if c.tag.split("}")[-1] == "name"), None)
            name = next(iter(name_el)).text if name_el is not None else el.get("id")
            names[el.get("id")] = name
            if tag == "place":
                im = next((c for c in el if c.tag.split("}")[-1] == "initialMarking"), None)
                places[name] = int(next(iter(im)).text) if im is not None else 0
            else:
                transitions.append(name)
    for el in root.iter():
        if el.tag.split("}")[-1] != "arc":
            continue
        weight, kind = 1, "normal"
        for c in el:
            t = c.tag.split("}")[-1]
            if t == "inscription":
                weight = int(next(iter(c)).text)
            elif t == "type":
                kind = {"test": "read", "inhibitor": "inhibit"}.get(c.get("value"), "normal")
        arcs.append((names[el.get("source")], names[el.get("target")], weight, kind))
    return {"places": places, "transitions": transitions, "arcs": arcs}


def expand_plain(net: PetriNet) -> PetriNet:
    out = PetriNet(net.name + "_plain", halting=False, derived=net.derived)
    for p in net.places.values():
        out.places[p.id] = NetPlace(p.id, p.kind, p.origin, p.initial, None, False, p.terminal, p.label)
        if p.once:
            out.places[p.id + "^"] = NetPlace(p.id + "^", "control", p.origin, 0 if p.initial else 1, None)
        if p.capacity is not None and not p.once:
            out.places[p.id + "~"] = NetPlace(p.id + "~", "control", p.origin, p.capacity - p.initial, None)
    if net.halting:
        out.places["halt"] = NetPlace("halt", "control", "", 0, None)

    for t in net.transitions:
        once_outs = [a for a in t.outputs if net.places[a.place].once]
        variants = product((True, False), repeat=len(once_outs)) if once_outs else [()]
        for fresh_flags in variants:
            fresh = dict(zip((a.place for a in once_outs), fresh_flags))
            ins = [NetArc(a.place, a.weight, a.kind) for a in t.inputs]
            outs: list[NetArc] = []
            # Capacity complements follow the *net* change of each place, so a
            # self-loop (take one, put one back) needs no free room -- the same
            # rule as TokenGame.enabled (m - consumed + produced <= capacity).
            delta: dict[str, int] = {}
            for a in t.inputs:
                if a.kind == "normal":
                    delta[a.place] = delta.get(a.place, 0) - a.weight
            for a in t.outputs:
                if not net.places[a.place].once:
                    delta[a.place] = delta.get(a.place, 0) + a.weight
            for place, d in delta.items():
                p = net.places[place]
                if p.capacity is None or p.once or d == 0:
                    continue
                (ins if d > 0 else outs).append(NetArc(place + "~", abs(d)))
            for a in t.outputs:
                p = net.places[a.place]
                if p.once:
                    if fresh[a.place]:
                        ins.append(NetArc(a.place + "^", 1))
                        outs.append(NetArc(a.place, a.weight))
                    else:
                        ins.append(NetArc(a.place + "^", 1, "inhibit"))
                    continue
                outs.append(NetArc(a.place, a.weight))
            if net.halting:
                ins.append(NetArc("halt", 1, "inhibit"))
                if any(net.places[a.place].terminal and fresh.get(a.place, True) for a in t.outputs):
                    outs.append(NetArc("halt", 1))
            suffix = "" if not once_outs else "#" + "".join("f" if f else "s" for f in fresh_flags)
            out.transitions.append(NetTransition(
                t.id + suffix, t.origin, t.dispatch, _merge(ins), _merge(outs), t.priority, t.order,
                silent=t.silent, trigger=t.trigger, guard_static=None if t.guard_static is not False else False))
    return out


def _merge(arcs: list[NetArc]) -> list[NetArc]:
    """Combine normal arcs to the same place (a refill and a take cancel out
    only in the firing rule, so keep both directions separate)."""
    merged: dict[tuple[str, str], int] = {}
    order: list[tuple[str, str]] = []
    for a in arcs:
        k = (a.place, a.kind)
        if k not in merged:
            order.append(k)
            merged[k] = 0
        merged[k] = max(merged[k], a.weight) if a.kind != "normal" else merged[k] + a.weight
    return [NetArc(p, merged[(p, kind)], kind) for p, kind in order]


def plain_reachability(net: PetriNet, limit: int = 200_000) -> set[tuple[tuple[str, int], ...]]:
    """Reachable markings of a plain net under interleaving semantics, every
    guard free (static-false transitions excluded). Markings are sorted
    (place, tokens) tuples of the marked places."""
    places = list(net.places)
    idx = {p: i for i, p in enumerate(places)}
    ts = [t for t in net.transitions if t.guard_static is not False]
    init = tuple(net.places[p].initial for p in places)
    seen = {init}
    stack = [init]
    while stack and len(seen) < limit:
        m = stack.pop()
        for t in ts:
            ok = True
            for a in t.inputs:
                v = m[idx[a.place]]
                if (a.kind in ("normal", "read") and v < a.weight) or (a.kind == "inhibit" and v >= a.weight):
                    ok = False
                    break
            if not ok:
                continue
            nm = list(m)
            for a in t.inputs:
                if a.kind == "normal":
                    nm[idx[a.place]] -= a.weight
            for a in t.outputs:
                nm[idx[a.place]] += a.weight
            nm = tuple(nm)
            if nm not in seen:
                seen.add(nm)
                stack.append(nm)
    return {tuple((places[i], v) for i, v in enumerate(m) if v) for m in seen}
