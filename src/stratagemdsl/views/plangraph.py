"""PlanGraph views of the plan's Petri net (layer 8).

`build_graph_model(strategy)` gathers, for every place and transition of the
compiled net:

  * the DSL node it implements (silent join machinery is marked as such),
  * the validator diagnostics that name it,
  * the net analysis result -- token bound, never marked, never fires,
  * how the backend dispatches it (event trigger / immediate / periodic poll)
    or why it failed to lower.

Three renderings share that model:

  to_net_dot    bipartite Petri net (places = circles with tokens, transitions =
                bars, read arcs dashed, inhibitor arcs with a circle head)
  to_dot        the compact PlanGraph (DSL nodes, transitions as edges); a
                multi-input/multi-output transition is drawn as a small bar
  to_mermaid    the compact PlanGraph for mermaid.js
"""
from __future__ import annotations

import html
from dataclasses import dataclass, field
from typing import Optional

from stratagemdsl.core.model import Expr, Strategy
from stratagemdsl.frontend.unparse import _print_expr
from stratagemdsl.semantics.validator import Validator


@dataclass
class PlaceInfo:
    id: str
    kind: str              # phase | join | join_input | join_arrivals | join_armed | resource
    origin: str
    label: str
    tokens: int = 0
    capacity: Optional[int] = None
    once: bool = False
    terminal: Optional[str] = None
    bound: Optional[int] = None
    never_marked: bool = False
    warnings: list[str] = field(default_factory=list)

    @property
    def is_start(self) -> bool:
        return self.tokens > 0 and self.kind == "phase"


@dataclass
class TransitionInfo:
    id: str
    origin: Optional[str]
    dispatch: str          # event | immediate | polled
    label: str
    priority: int
    silent: bool = False
    lowering_kind: str = "unknown"
    error_message: str = ""
    dead: bool = False
    warnings: list[str] = field(default_factory=list)


@dataclass
class ArcInfo:
    place: str
    transition: str
    direction: str         # in | out
    weight: int = 1
    kind: str = "normal"   # normal | read | inhibit


@dataclass
class GraphModel:
    name: str
    places: list[PlaceInfo]
    transitions: list[TransitionInfo]
    arcs: list[ArcInfo]
    lowering_ok: bool
    lowering_error: str = ""
    analysis: dict = field(default_factory=dict)
    diagnostics: list[str] = field(default_factory=list)

    # v0.5 compatibility: nodes/edges of the compact graph
    @property
    def nodes(self) -> list[PlaceInfo]:
        return [p for p in self.places if p.kind in ("phase", "join", "resource")]

    @property
    def edges(self) -> list[TransitionInfo]:
        return [t for t in self.transitions if not t.silent]


def _text(e: Optional[Expr]) -> str:
    if e is None:
        return ""
    try:
        return _print_expr(e)
    except Exception:
        return "<unprintable>"


def build_graph_model(strategy: Strategy) -> GraphModel:
    from stratagemdsl.backend.galaxy import GalaxyLowerer, LoweringError
    from stratagemdsl.net import analyze, build_net

    validator = Validator(strategy)
    bag = validator.validate()
    net = validator.net or build_net(strategy)
    report = validator.net_report
    if report is None:
        try:
            report = analyze(net)
        except Exception:
            report = None
    bounds = report.bound() if report else {}
    marked = report.marked() if report else set()
    fired = report.fired() if report else set()

    def mentions(name: str) -> list[str]:
        return [str(d) for d in bag.items if f"'{name}'" in d.message]

    places = [PlaceInfo(p.id, p.kind, p.origin, p.label, p.initial, p.capacity, p.once, p.terminal,
                        bounds.get(p.id), report is not None and p.id not in marked,
                        mentions(p.id) if p.is_control else [])
              for p in net.places.values()]

    lowering_ok, lowering_error, kinds = True, "", {}
    try:
        lowerer = GalaxyLowerer(strategy)
        try:
            lowerer.emit()
        finally:
            kinds = lowerer.transition_kinds
    except (LoweringError, ValueError, TypeError) as e:
        lowering_ok, lowering_error = False, str(e)

    transitions, arcs = [], []
    for t in net.transitions:
        parts = []
        if t.event is not None:
            parts.append("on " + _text(t.event))
        if t.guard is not None:
            parts.append("when " + _text(t.guard))
        if not t.silent:
            parts.append(f"p={t.priority}")
        info = kinds.get(t.id, {"kind": "unknown"})
        transitions.append(TransitionInfo(
            t.id, t.origin, t.dispatch, "\n".join(parts) if parts else t.note, t.priority, t.silent,
            info.get("kind", "unknown"), info.get("message", ""),
            report is not None and t.id not in fired, mentions(t.id) if t.origin else []))
        arcs += [ArcInfo(a.place, t.id, "in", a.weight, a.kind) for a in t.inputs]
        arcs += [ArcInfo(a.place, t.id, "out", a.weight) for a in t.outputs]
    return GraphModel(strategy.name, places, transitions, arcs, lowering_ok, lowering_error,
                      report.summary() if report else {}, [str(d) for d in bag.items])


# ------------------------------------------------------------------- styles
DISPATCH_STYLE = {
    "event": dict(color="black", fillcolor="#212121"),
    "immediate": dict(color="#2e7d32", fillcolor="#2e7d32"),
    "polled": dict(color="#e65100", fillcolor="#e65100"),
    "error": dict(color="#c62828", fillcolor="#c62828"),
    "unknown": dict(color="gray", fillcolor="gray"),
}
CAPTION = {
    "event": "event trigger",
    "immediate": "immediate (settle loop)",
    "polled": "periodic poll",
    "error": "FAILED TO LOWER",
    "unknown": "not lowered",
}


def _q(s: str) -> str:
    return s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")


def _tokens(n: int) -> str:
    return "●" * n if n <= 4 else f"{n}●"


def _style(t: TransitionInfo) -> dict:
    kind = t.lowering_kind if t.lowering_kind == "error" else t.dispatch
    return DISPATCH_STYLE.get(kind, DISPATCH_STYLE["unknown"])


def _place_attrs(p: PlaceInfo) -> str:
    label = p.id if p.kind in ("phase", "join", "resource") else p.id.split(".", 1)[-1]
    extra = []
    if p.tokens:
        label += "\\n" + _tokens(p.tokens)
    if p.capacity is not None and p.kind == "resource":
        label += f"\\ncap {p.capacity}"
    shape = "circle"
    if p.terminal == "success":
        extra.append('peripheries=2, color="#2e7d32"')
    elif p.terminal == "failure":
        extra.append('peripheries=2, color="#c62828"')
    elif p.kind == "join":
        shape = "doublecircle"
    elif p.kind == "resource":
        extra.append('style=filled, fillcolor="#e3f2fd"')
    elif p.kind in ("join_input", "join_arrivals", "join_armed"):
        extra.append('fontsize=8, width=0.35, color="#757575"')
    if p.never_marked:
        extra.append('style="dashed", fontcolor="#9e9e9e"')
    if p.warnings:
        extra.append('penwidth=2.5, color="#e65100", tooltip="' + _q("; ".join(p.warnings))[:400] + '"')
    return f'shape={shape}, label="{label}"' + (", " + ", ".join(extra) if extra else "")


def to_net_dot(model: GraphModel) -> str:
    lines = [f'digraph "{_q(model.name)}" {{', '  rankdir="LR";',
             '  node [fontname="Helvetica", fontsize=10];', '  edge [fontname="Helvetica", fontsize=9];']
    for p in model.places:
        lines.append(f'  "p:{_q(p.id)}" [{_place_attrs(p)}];')
    for t in model.transitions:
        st = _style(t)
        label = "" if t.silent else t.id
        xlabel = _q(t.label) + ("\\n[never fires]" if t.dead else "")
        attrs = [f'shape=box, style="filled{",dashed" if t.dead else ""}", height=0.45, width=0.08',
                 f'fillcolor="{st["fillcolor"] if not t.dead else "#bdbdbd"}"', f'color="{st["color"]}"',
                 f'label="", xlabel="{_q(label)}\\n{xlabel}"',
                 f'tooltip="{_q(t.id + ": " + CAPTION.get(t.lowering_kind, t.lowering_kind) + (" " + t.error_message if t.error_message else ""))}"']
        if t.silent:
            attrs[0] = 'shape=box, style="filled", height=0.3, width=0.05'
        lines.append(f'  "t:{_q(t.id)}" [{", ".join(attrs)}];')
    for a in model.arcs:
        w = f'label="{a.weight}"' if a.weight != 1 else ""
        if a.direction == "out":
            lines.append(f'  "t:{_q(a.transition)}" -> "p:{_q(a.place)}" [{w}];')
        elif a.kind == "read":
            lines.append(f'  "p:{_q(a.place)}" -> "t:{_q(a.transition)}" [style=dashed, dir=both, arrowtail=none, arrowhead=none{", " + w if w else ""}];')
        elif a.kind == "inhibit":
            lines.append(f'  "p:{_q(a.place)}" -> "t:{_q(a.transition)}" [arrowhead=odot, color="#c62828"{", " + w if w else ""}];')
        else:
            lines.append(f'  "p:{_q(a.place)}" -> "t:{_q(a.transition)}" [{w}];')
    if not model.lowering_ok:
        lines.append(f'  "__lowering_error__" [shape=note, color="#c62828", fontcolor="#c62828", label="LOWERING FAILED:\\n{_q(model.lowering_error[:200])}"];')
    lines.append("}")
    return "\n".join(lines)


def _compact(model: GraphModel):
    """DSL-level view: join machinery folded back into its join node."""
    visible = {p.id for p in model.nodes}
    origin = {p.id: p.origin for p in model.places}

    def fold(place: str) -> str:
        return place if place in visible else origin.get(place, place)

    edges = []
    for t in model.edges:
        ins = [fold(a.place) for a in model.arcs if a.transition == t.id and a.direction == "in"]
        in_kinds = {fold(a.place): a.kind for a in model.arcs if a.transition == t.id and a.direction == "in"}
        outs = [fold(a.place) for a in model.arcs if a.transition == t.id and a.direction == "out"]
        edges.append((t, ins, outs, in_kinds))
    return edges


def to_dot(model: GraphModel) -> str:
    lines = ['digraph PlanGraph {', '  rankdir="LR";', '  node [fontname="Helvetica", fontsize=11];',
             '  edge [fontname="Helvetica", fontsize=9];', '  "__start__" [shape=point];']
    for p in model.nodes:
        if p.is_start:
            lines.append(f'  "__start__" -> "{_q(p.id)}";')
    for p in model.nodes:
        shape = {"join": "diamond", "resource": "cylinder"}.get(p.kind, "box")
        if p.terminal == "success":
            shape = 'box, peripheries=2, color="#2e7d32"'
        elif p.terminal == "failure":
            shape = 'box, peripheries=2, color="#c62828"'
        label = p.id + "\\n" + _q(p.label[:48] + ("…" if len(p.label) > 48 else ""))
        if p.kind == "resource":
            label += f"\\n{_tokens(p.tokens)}" + (f" / cap {p.capacity}" if p.capacity is not None else "")
        extra = ""
        if p.warnings:
            extra = ', color="#e65100", penwidth=2, tooltip="' + _q("; ".join(p.warnings))[:400] + '"'
        if p.never_marked:
            extra += ", style=dashed"
        lines.append(f'  "{_q(p.id)}" [shape={shape}, label="{label}"{extra}];')
    for t, ins, outs, in_kinds in _compact(model):
        st = _style(t)
        caption = CAPTION.get(t.lowering_kind, t.lowering_kind) + (" · never fires" if t.dead else "")
        label = _q(t.id + "\n" + t.label) + f"\\n[{caption}]"
        if t.error_message:
            label += "\\n" + _q(t.error_message[:80])
        style = f'color="{st["color"]}", style="{"dashed" if t.dead else "solid"}", penwidth=1.6'
        if len(ins) == 1 and len(outs) == 1 and in_kinds[ins[0]] == "normal":
            lines.append(f'  "{_q(ins[0])}" -> "{_q(outs[0])}" [label="{label}", {style}];')
            continue
        bar = f"t:{t.id}"
        lines.append(f'  "{_q(bar)}" [shape=box, label="", xlabel="{label}", width=0.06, height=0.4, style=filled, fillcolor="{st["fillcolor"]}"];')
        for x in ins:
            k = in_kinds[x]
            arrow = {"read": 'style=dashed, arrowhead=none', "inhibit": 'arrowhead=odot, color="#c62828"'}.get(k, "")
            lines.append(f'  "{_q(x)}" -> "{_q(bar)}" [{arrow}];')
        for x in outs:
            lines.append(f'  "{_q(bar)}" -> "{_q(x)}";')
    if not model.lowering_ok:
        lines.append(f'  "__lowering_error__" [shape=note, color="#c62828", fontcolor="#c62828", label="LOWERING FAILED:\\n{_q(model.lowering_error[:200])}"];')
    lines.append("}")
    return "\n".join(lines)


def to_mermaid(model: GraphModel) -> str:
    def sid(x: str) -> str:
        return "n_" + "".join(c if c.isalnum() else "_" for c in x)

    lines = ["flowchart LR", '  start((" ")):::startKind']
    link_styles: list[str] = []
    link = 0
    for p in model.nodes:
        if p.is_start:
            lines.append(f"  start --> {sid(p.id)}")
            link += 1
    for p in model.nodes:
        label = html.escape(f"{p.id}: {p.label[:60]}")
        if p.kind == "resource":
            label += html.escape(f" [{p.tokens}" + (f"/{p.capacity}]" if p.capacity is not None else "]"))
            shape = f'{sid(p.id)}[("{label}")]'
        elif p.kind == "join":
            shape = f'{sid(p.id)}{{"{label}"}}'
        elif p.terminal == "success":
            shape = f'{sid(p.id)}(["{label}"])'
        elif p.terminal == "failure":
            shape = f'{sid(p.id)}[/"{label}"/]'
        else:
            shape = f'{sid(p.id)}["{label}"]'
        lines.append(f"  {shape}")
        if p.warnings:
            lines.append(f"  class {sid(p.id)} warnNode")
    style = {
        "event": "stroke:#000000,stroke-width:2px",
        "immediate": "stroke:#2e7d32,stroke-width:2px,stroke-dasharray:4 2",
        "polled": "stroke:#e65100,stroke-width:2px,stroke-dasharray:1 2",
        "error": "stroke:#c62828,stroke-width:3px",
        "unknown": "stroke:#9e9e9e,stroke-width:1px",
    }
    for t, ins, outs, in_kinds in _compact(model):
        kind = t.lowering_kind if t.lowering_kind == "error" else t.dispatch
        label = "<br/>".join(html.escape(x) for x in (t.id + "\n" + t.label).split("\n") + [f"[{CAPTION.get(kind, kind)}]"])
        if len(ins) == 1 and len(outs) == 1 and in_kinds[ins[0]] == "normal":
            lines.append(f'  {sid(ins[0])} -->|"{label}"| {sid(outs[0])}')
            link_styles.append(f"  linkStyle {link} {style.get(kind, style['unknown'])};")
            link += 1
            continue
        bar = sid("t_" + t.id)
        lines.append(f'  {bar}[["{label}"]]')
        for x in ins:
            arrow = {"read": "-.->", "inhibit": "--o"}.get(in_kinds[x], "-->")
            lines.append(f"  {sid(x)} {arrow} {bar}")
            link += 1
        for x in outs:
            lines.append(f"  {bar} --> {sid(x)}")
            link += 1
    lines.extend(link_styles)
    lines.append("  classDef startKind fill:#333,stroke:#333;")
    lines.append("  classDef warnNode stroke:#e65100,stroke-width:3px;")
    if not model.lowering_ok:
        lines.append(f'  err_note["LOWERING FAILED:<br/>{html.escape(model.lowering_error[:200])}"]')
    return "\n".join(lines)


# ------------------------------------------------------------------ files
def render_svg(dot_text: str) -> Optional[str]:
    """SVG via Graphviz `dot` when it is installed, else None."""
    import shutil
    import subprocess
    exe = shutil.which("dot")
    if exe is None:
        return None
    # Graphviz reads and writes UTF-8; the platform default (GBK on a Chinese
    # Windows) would garble Chinese labels.
    r = subprocess.run([exe, "-Tsvg"], input=dot_text, capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=120)
    return r.stdout if r.returncode == 0 else None


def write_views(strategy: Strategy, out, stem: Optional[str] = None, *, svg: bool = True) -> dict:
    """PlanGraph (compact), PetriNet (bipartite), Mermaid, JSON and PNML files."""
    import json
    from dataclasses import asdict
    from pathlib import Path

    from stratagemdsl.net import build_net
    from stratagemdsl.net.pnml import to_pnml

    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    stem = stem or strategy.name
    model = build_graph_model(strategy)
    files = {
        f"{stem}.PlanGraph.dot": to_dot(model),
        f"{stem}.PetriNet.dot": to_net_dot(model),
        f"{stem}.PlanGraph.mmd": to_mermaid(model),
        f"{stem}.PlanGraph.json": json.dumps(asdict(model), ensure_ascii=False, indent=2, default=str),
        f"{stem}.pnml": to_pnml(build_net(strategy)),
    }
    if svg:
        for name in (f"{stem}.PlanGraph.dot", f"{stem}.PetriNet.dot"):
            text = render_svg(files[name])
            if text:
                files[name.removesuffix(".dot") + ".svg"] = text
    for name, text in files.items():
        (out / name).write_text(text, encoding="utf-8")
    return {"model": model, "files": sorted(files)}
