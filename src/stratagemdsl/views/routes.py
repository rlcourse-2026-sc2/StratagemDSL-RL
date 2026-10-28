"""Movement routes of a strategy on a base map (`strat route`).

Where does each force go, along which ground path, over which ramps? The
legs come from the plan, the paths from the map's terrain:

1. **Legs.** Every movement action (`move`, `retreat`, `attack`, `retarget`,
   `block`, `cast` with a target) gives a destination for its force. Where the
   force *starts* that leg is found by a forward dataflow over the plan graph
   (phase -> transition -> phase, cycles included): a force is at its spawn
   point in the initial marking and at the destination of its last movement
   afterwards. Branches merge as sets, so every leg that some run of the plan
   can produce is listed once.
2. **Paths.** A* on the terrain grid read from the map (`packaging.terrain`):
   8-neighbour moves, a step only between cells of the same cliff level or
   through a ramp, no corner cutting, void cells and the cells of blocking
   doodads/placed units are impassable. A leg to a region ends where the path
   enters the region (that is when `enter(...)` fires); a leg to an entity ends
   within reach of it. Air units fly straight.

This approximates pathing from cliff levels and doodad positions: the real
pathing grid is computed by the editor and is not stored in the map archive,
and unit size, footprints of units spawned at run time and blocking by other
units are ignored. A route proves the terrain is connected, not that the
engine's pathfinder takes this exact line.
"""
from __future__ import annotations

import heapq
import html
import json
import math
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Optional

from stratagemdsl.core.model import ActionBlock, BindingCall, CallExpr, NameExpr, Phase, Strategy
from stratagemdsl.packaging.terrain import FOOTPRINT, RAMP, VOID, MapProfile, load_profile

MOVEMENT = {"move", "retreat", "attack", "retarget", "block", "cast"}
AIR_UNITS = {
    "Medivac", "VikingFighter", "Banshee", "Raven", "Liberator", "Battlecruiser", "Mutalisk", "Corruptor",
    "BroodLord", "Overlord", "Overseer", "OverlordTransport", "Phoenix", "VoidRay", "Oracle", "Tempest",
    "Carrier", "Observer", "WarpPrism", "Mothership", "Viper", "Interceptor",
}
REACH = 1.5   # an attack/retarget leg ends this many cells from the target (plus its footprint)


# ------------------------------------------------------------------ data
@dataclass
class Location:
    name: str
    x: float
    y: float
    radius: float = 0.0      # > 0 for a region: the leg ends on entering it
    footprint: float = 0.0   # half size of a structure at this point
    kind: str = "point"      # spawn | region | entity
    side: str = ""           # ally | enemy for forces and assets


@dataclass
class RouteLeg:
    force: str
    side: str
    unit_types: list[str]
    air: bool
    context: str             # "phase feint" | "transition threat"
    action: str              # the DSL call, e.g. move(feint_force, main_threat_zone)
    origin: str
    target: str
    status: str              # ok | air | unreachable | already_there | no_position
    length: float = 0.0      # cells (diagonal step = 1.414)
    ramps: list[str] = field(default_factory=list)
    plateaus: list[str] = field(default_factory=list)
    path: list[tuple[float, float]] = field(default_factory=list)
    note: str = ""


@dataclass
class RoutePlan:
    strategy: str
    map: str
    size: tuple[int, int]
    locations: dict[str, Location]
    legs: list[RouteLeg]
    warnings: list[str]

    def to_dict(self) -> dict:
        out = asdict(self)
        out["format"] = "stratagemdsl.routes.v1"
        out["scope"] = ("ground paths approximated from cliff levels and doodads; "
                        "not the engine's pathfinder")
        return out


# ------------------------------------------------------------ bindings
def _arg(call: BindingCall, name: str, index: Optional[int] = None):
    v = next((a.value for a in call.args if a.name == name), None)
    if v is None and index is not None:
        pos = [a.value for a in call.args if a.name is None]
        v = pos[index] if index < len(pos) else None
    return v


def _point(value, profile: MapProfile) -> Optional[tuple[float, float]]:
    if not isinstance(value, BindingCall):
        return None
    if value.name == "point_xy":
        x, y = _arg(value, "x", 0), _arg(value, "y", 1)
        return (float(x), float(y)) if isinstance(x, (int, float)) and isinstance(y, (int, float)) else None
    if value.name == "point_id":
        pid = _arg(value, "id", 0)
        return profile.point_ids.get(int(pid)) if isinstance(pid, (int, float)) else None
    return None


def _unit_types(call: BindingCall) -> list[str]:
    out = []
    if isinstance(_arg(call, "unit_type"), str):
        out.append(_arg(call, "unit_type"))
    for item in _arg(call, "composition") or []:
        if isinstance(item, BindingCall) and isinstance(_arg(item, "unit_type"), str):
            out.append(_arg(item, "unit_type"))
    return out


def resolve_locations(strategy: Strategy, profile: MapProfile) -> tuple[dict[str, Location], dict[str, list[str]]]:
    """Coordinates of every bound force, asset and region; unit types per force."""
    kinds = {e.name: e.kind for e in strategy.world}
    sides = {e.name: str(e.properties.get("side", "")).strip('"') for e in strategy.world}
    locs: dict[str, Location] = {}
    types: dict[str, list[str]] = {}
    for b in strategy.bindings:
        v = b.value
        if b.name == "__setup__" or not isinstance(v, BindingCall):
            continue
        kind = kinds.get(b.name)
        if kind in ("force", "asset"):
            types[b.name] = _unit_types(v)
            p = _point(_arg(v, "spawn"), profile) or _point(_arg(v, "at"), profile)
            if p is None:
                first = next((i for i in (_arg(v, "composition") or []) if isinstance(i, BindingCall)), None)
                p = _point(_arg(first, "at"), profile) if first else None
            if p is not None:
                half = max((FOOTPRINT.get(t, 0.0) for t in types[b.name]), default=0.0) if kind == "asset" else 0.0
                locs[b.name] = Location(b.name, p[0], p[1], footprint=half, kind="entity", side=sides[b.name])
        elif kind == "region":
            if v.name == "circle":
                c = _point(_arg(v, "center", 0), profile)
                r = _arg(v, "radius", 1)
                if c is not None:
                    locs[b.name] = Location(b.name, c[0], c[1], radius=float(r or 1.0), kind="region")
            elif v.name == "rect":
                xs = [_arg(v, n, i) for i, n in enumerate(("x0", "y0", "x1", "y1"))]
                if all(isinstance(x, (int, float)) for x in xs):
                    cx, cy = (xs[0] + xs[2]) / 2, (xs[1] + xs[3]) / 2
                    locs[b.name] = Location(b.name, cx, cy, radius=min(abs(xs[2] - xs[0]), abs(xs[3] - xs[1])) / 2,
                                            kind="region")
    return locs, types


# ------------------------------------------------------------ legs
def _destination(call: CallExpr) -> Optional[tuple[str, str]]:
    """(force, target name) of a movement action."""
    if call.name not in MOVEMENT or not call.args or not isinstance(call.args[0], NameExpr):
        return None
    targets = [a.name for a in call.args[1:] if isinstance(a, NameExpr)]
    return (call.args[0].name, targets[-1]) if targets else None


def _contexts(strategy: Strategy):
    """Plan graph for the dataflow: node -> successors, action block, (force, region) pinned by `on enter`."""
    plan = strategy.plan
    succ: dict[str, set[str]] = {}
    blocks: dict[str, Optional[ActionBlock]] = {}
    pins: dict[str, tuple[str, str]] = {}
    weak: set[tuple[str, str]] = set()    # read arcs and inputs from non-phase places
    for n in plan.nodes:
        key = f"phase {n.id}" if isinstance(n, Phase) else f"node {n.id}"
        blocks[key] = getattr(n, "actions", None)
        succ.setdefault(key, set())
    node_key = {n.id: (f"phase {n.id}" if isinstance(n, Phase) else f"node {n.id}") for n in plan.nodes}
    for t in plan.transitions:
        tk = f"transition {t.id}"
        blocks[tk] = t.actions
        succ.setdefault(tk, set())
        ev = t.event
        if isinstance(ev, CallExpr) and ev.name == "enter" and len(ev.args) >= 2 and \
                all(isinstance(a, NameExpr) for a in ev.args[:2]):
            pins[tk] = (ev.args[0].name, ev.args[1].name)
        for a in t.inputs:
            if a.kind != "inhibit" and a.place in node_key:
                succ[node_key[a.place]].add(tk)
                if a.kind == "read" or not node_key[a.place].startswith("phase "):
                    weak.add((node_key[a.place], tk))
        for a in t.outputs:
            if a.place in node_key:
                succ[tk].add(node_key[a.place])
    roots = [node_key[s] for s in plan.start if s in node_key]
    roots += [node_key[n.id] for n in plan.nodes if getattr(n, "tokens", 0)]
    return succ, blocks, roots, pins, weak


def plan_legs(strategy: Strategy, forces: list[str]):
    """[(force, context, action, origin, target)] for every reachable movement.

    Position of a force along the plan graph:
      * a start phase that moves the force starts it at its spawn point; every
        other start branch sees it where the start phases send it (the start
        phases run concurrently from time 0);
      * `on enter(F, R)` puts F in R for the transition and everything after it;
      * a transition takes positions from the phases it consumes; read arcs and
        resource places only fill in forces those phases know nothing about;
      * after `move/attack/...(F, X)` F is at X; when X is a force, at that
        force's position at that point (so "attack the returning siege force"
        ends where the siege force was last seen).
    Branches merge as sets; every combination yields one leg."""
    from stratagemdsl.frontend.unparse import _print_expr
    succ, blocks, roots, pins, weak = _contexts(strategy)
    pred: dict[str, set[str]] = {k: set() for k in succ}
    for u, vs in succ.items():
        for v in vs:
            pred[v].add(u)
    fset = {e.name for e in strategy.world if e.kind == "force"} & set(forces)   # assets do not move

    def moves(key):
        block = blocks.get(key)
        return [(d, a) for a in (block.actions if block else []) if (d := _destination(a))]

    def resolve(target: str, current: dict, seen=()) -> frozenset:
        if target not in fset or target in seen:
            return frozenset({target})
        here = current.get(target) or {f"spawn:{target}"}
        return frozenset().union(*(resolve(p, current, seen + (target,)) for p in here))

    spawn = {f: frozenset({f"spawn:{f}"}) for f in forces}
    background = dict(spawn)
    for r in roots:
        cur = {f: set(spawn[f]) for f in forces}
        for (force, target), _a in moves(r):
            if force in cur:
                cur[force] = set(resolve(target, cur))
                background[force] = frozenset(cur[force])
    root_in = {r: {f: (spawn[f] if any(m[0][0] == f for m in moves(r)) else background[f]) for f in forces}
               for r in roots}

    def run_node(k, pos_in):
        cur = {f: set(v) for f, v in pos_in.items()}
        if k in pins and pins[k][0] in cur:
            cur[pins[k][0]] = {pins[k][1]}
        legs = []
        for (force, target), action in moves(k):
            if force not in cur:
                continue
            dest = resolve(target, cur)
            for origin in sorted(cur[force]) or ["(unknown)"]:
                for d in sorted(dest):
                    if origin != d:      # e.g. a later round of a cycle: already there
                        legs.append((force, k, _print_expr(action), origin, d))
            cur[force] = set(dest)
        return {f: frozenset(v) for f, v in cur.items()}, legs

    pos_in: dict[str, dict[str, frozenset]] = {k: {f: frozenset() for f in forces} for k in succ}
    pos_out: dict[str, dict[str, frozenset]] = {k: {f: frozenset() for f in forces} for k in succ}
    changed = True
    while changed:
        changed = False
        for k in succ:
            base = root_in.get(k, {f: frozenset() for f in forces})
            strong = [p for p in pred[k] if (p, k) not in weak]
            soft = [p for p in pred[k] if (p, k) in weak]
            new_in = {}
            for f in forces:
                v = base[f].union(*(pos_out[p][f] for p in strong))
                new_in[f] = v or base[f].union(*(pos_out[p][f] for p in soft))
            new_out, _ = run_node(k, new_in)
            if new_in != pos_in[k] or new_out != pos_out[k]:
                pos_in[k], pos_out[k], changed = new_in, new_out, True
    seen, out = set(), []
    for k in succ:
        for leg in run_node(k, pos_in[k])[1]:
            key = (leg[0], leg[3], leg[4])
            if key not in seen:
                seen.add(key)
                out.append(leg)
    return out


# ------------------------------------------------------------ pathfinding
class Grid:
    def __init__(self, profile: MapProfile):
        self.p = profile
        self.blocked = {(int(math.floor(x)), int(math.floor(y))) for x, y, _ in profile.blockers}

    def passable(self, i: int, j: int) -> bool:
        v = self.p.cell(i + 0.5, j + 0.5)
        return v not in (None, VOID) and (i, j) not in self.blocked

    def step_ok(self, a: tuple[int, int], b: tuple[int, int]) -> bool:
        la, lb = self.p.level[a[1]][a[0]], self.p.level[b[1]][b[0]]
        return la == lb or RAMP in (la, lb)

    def neighbours(self, u: tuple[int, int]):
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)):
            v = (u[0] + dx, u[1] + dy)
            if not self.passable(*v) or not self.step_ok(u, v):
                continue
            if dx and dy:   # no corner cutting
                a, b = (u[0] + dx, u[1]), (u[0], u[1] + dy)
                if not (self.passable(*a) and self.passable(*b) and self.step_ok(u, a) and self.step_ok(u, b)):
                    continue
            yield v, (math.sqrt(2) if dx and dy else 1.0)

    def snap(self, x: float, y: float, radius: int = 4) -> Optional[tuple[int, int]]:
        best = None
        for j in range(int(y) - radius, int(y) + radius + 1):
            for i in range(int(x) - radius, int(x) + radius + 1):
                if self.passable(i, j):
                    d = math.hypot(i + 0.5 - x, j + 0.5 - y)
                    if best is None or d < best[0]:
                        best = (d, (i, j))
        return best[1] if best else None

    def astar(self, start: tuple[int, int], goal: Location, stop: float) -> Optional[list[tuple[int, int]]]:
        def h(c):
            return max(0.0, math.hypot(c[0] + 0.5 - goal.x, c[1] + 0.5 - goal.y) - stop)
        best = {start: 0.0}
        prev = {start: None}
        heap = [(h(start), 0.0, start)]
        while heap:
            _f, g, u = heapq.heappop(heap)
            if g > best.get(u, math.inf):
                continue
            if h(u) == 0.0:
                out = []
                while u is not None:
                    out.append(u)
                    u = prev[u]
                return out[::-1]
            for v, w in self.neighbours(u):
                ng = g + w
                if ng < best.get(v, math.inf):
                    best[v], prev[v] = ng, u
                    heapq.heappush(heap, (ng + h(v), ng, v))
        return None


def _ramp_of(profile: MapProfile, i: int, j: int) -> Optional[str]:
    if not profile.ramps:
        return None
    return min(profile.ramps, key=lambda r: math.hypot(r.center[0] - i - 0.5, r.center[1] - j - 0.5)).rid


def plan_routes(strategy: Strategy, profile: MapProfile) -> RoutePlan:
    locs, types = resolve_locations(strategy, profile)
    sides = {e.name: e.properties.get("side", "") for e in strategy.world}
    forces = [e.name for e in strategy.world if e.kind in ("force", "asset")]
    for f in forces:
        if f in locs:
            locs[f"spawn:{f}"] = Location(f"spawn:{f}", locs[f].x, locs[f].y, kind="spawn")
    grid = Grid(profile)
    legs, warnings = [], []
    for force, context, action, origin, target in plan_legs(strategy, forces):
        ut = types.get(force, [])
        air = bool(ut) and all(t in AIR_UNITS for t in ut)
        leg = RouteLeg(force, str(sides.get(force, "")), ut, air, context, action, origin, target, "no_position")
        a, b = locs.get(origin), locs.get(target)
        if a is None or b is None:
            leg.note = f"no coordinates for {origin if a is None else target}"
            legs.append(leg)
            continue
        stop = b.radius if b.kind == "region" else b.footprint + REACH
        if math.hypot(a.x - b.x, a.y - b.y) <= stop:
            leg.status, leg.path = "already_there", [(a.x, a.y)]
            legs.append(leg)
            continue
        if air:
            d = math.hypot(a.x - b.x, a.y - b.y)
            frac = (d - stop) / d
            leg.status, leg.length = "air", round(d - stop, 1)
            leg.path = [(a.x, a.y), (round(a.x + (b.x - a.x) * frac, 2), round(a.y + (b.y - a.y) * frac, 2))]
            legs.append(leg)
            continue
        s = grid.snap(a.x, a.y)
        cells = grid.astar(s, b, stop) if s else None
        if not cells:
            leg.status = "unreachable"
            leg.note = f"no ground path from {origin} ({a.x:g}, {a.y:g}) to {target} ({b.x:g}, {b.y:g})"
            warnings.append(f"{force}: {leg.note} [{context}]")
            legs.append(leg)
            continue
        leg.status = "ok"
        leg.path = [(a.x, a.y)] + [(i + 0.5, j + 0.5) for i, j in cells[1:]]
        leg.length = round(sum(math.hypot(p[0] - q[0], p[1] - q[1]) for p, q in zip(cells, cells[1:])), 1)
        for i, j in cells:
            if profile.level[j][i] == RAMP:
                r = _ramp_of(profile, i, j)
                if r and (not leg.ramps or leg.ramps[-1] != r):
                    leg.ramps.append(r)
            reg = profile.region_at(i + 0.5, j + 0.5)
            if reg and (not leg.plateaus or leg.plateaus[-1] != reg):
                leg.plateaus.append(reg)
        legs.append(leg)
    for name, loc in locs.items():
        if loc.kind == "region" and not profile.walkable(loc.x, loc.y) and \
                not any(profile.walkable(loc.x + dx, loc.y + dy) for dx in (-loc.radius, loc.radius) for dy in (0,)):
            warnings.append(f"region {name} centre ({loc.x:g}, {loc.y:g}) is not on walkable ground")
    return RoutePlan(strategy.name, profile.path.name, (profile.width, profile.height),
                     {k: v for k, v in locs.items() if not k.startswith("spawn:")}, legs, warnings)


# ------------------------------------------------------------ rendering
TERRAIN = {VOID: "#3b3b3b", RAMP: "#dcc48c", 1: "#cfe0c6", 2: "#a3c49d", 3: "#73a06d", 4: "#4f7d4a"}
SIDE = {"ally": "#1f5fbf", "enemy": "#b3261e"}
PALETTE = {"ally": ["#1f5fbf", "#2ca02c", "#17becf", "#9467bd"],      # our side: blues and greens
           "enemy": ["#d62728", "#ff7f0e", "#8c564b", "#e377c2"],     # enemy: reds and oranges
           "": ["#555555", "#888888"]}
STRUCTURE = {"ally": "#1f3f7a", "enemy": "#7a1f1f"}


def _colours(plan: RoutePlan) -> dict[str, str]:
    forces = list(dict.fromkeys(l.force for l in plan.legs))
    side = {l.force: l.side if l.side in PALETTE else "" for l in plan.legs}
    out, used = {}, {k: 0 for k in PALETTE}
    for f in forces:
        pal = PALETTE[side[f]]
        out[f] = pal[used[side[f]] % len(pal)]
        used[side[f]] += 1
    return out


def to_svg(plan: RoutePlan, profile: MapProfile) -> str:
    W, H = profile.width, profile.height
    s = max(4.0, min(10.0, 760 / max(W, H)))
    legend_h = 22 * (len([l for l in plan.legs if l.status != "already_there"]) + 2)
    mw, mh = W * s, H * s
    def X(x): return round(x * s, 1)
    def Y(y): return round((H - y) * s, 1)
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {mw + 20:.0f} {mh + legend_h + 40:.0f}" '
           f'font-family="Helvetica, Arial, sans-serif" font-size="11">',
           f'<text x="10" y="18" font-size="14" font-weight="600">{html.escape(plan.strategy)} on {html.escape(plan.map)}</text>',
           f'<g transform="translate(10,28)">',
           f'<clipPath id="map"><rect width="{mw}" height="{mh}"/></clipPath>',
           '<g clip-path="url(#map)">', '<g shape-rendering="crispEdges">']
    for j in range(H):
        i = 0
        while i < W:
            v = profile.level[j][i]
            k = i
            while k + 1 < W and profile.level[j][k + 1] == v:
                k += 1
            out.append(f'<rect x="{X(i)}" y="{Y(j + 1)}" width="{round((k - i + 1) * s, 1)}" height="{round(s, 1)}" '
                       f'fill="{TERRAIN.get(v, "#888")}"/>')
            i = k + 1
    out.append('</g>')
    for bx, by, _n in profile.blockers:
        out.append(f'<text x="{X(bx)}" y="{Y(by) + 3}" text-anchor="middle" font-size="{s:.0f}" fill="#555" '
                   f'fill-opacity="0.6">×</text>')
    for r in profile.ramps:
        out.append(f'<text x="{X(r.center[0])}" y="{Y(r.center[1]) + 4}" text-anchor="middle" font-weight="600" '
                   f'fill="#7a5c00">{r.rid}</text>')
    for loc in plan.locations.values():
        if loc.kind == "region":
            out.append(f'<circle cx="{X(loc.x)}" cy="{Y(loc.y)}" r="{loc.radius * s:.1f}" fill="none" stroke="#222" '
                       f'stroke-dasharray="5 4" stroke-width="1.5"/>')
            ty = Y(loc.y + loc.radius) - 4 if loc.y + loc.radius < H - 1 else Y(loc.y - loc.radius) + 14
            out.append(f'<text x="{X(min(max(loc.x, 6), W - 6))}" y="{ty}" text-anchor="middle" font-weight="600">'
                       f'{html.escape(loc.name)}</text>')
    colours = _colours(plan)
    out.append('<defs>' + "".join(
        f'<marker id="arr{i}" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="5" markerHeight="5" orient="auto">'
        f'<path d="M0 0L10 5L0 10z" fill="{c}"/></marker>' for i, c in enumerate(colours.values())) + '</defs>')
    index = {f: i for i, f in enumerate(colours)}
    for leg in plan.legs:
        if len(leg.path) < 2:
            continue
        pts = " ".join(f"{X(x)},{Y(y)}" for x, y in leg.path)
        dash = ' stroke-dasharray="6 4"' if leg.air else ""
        out.append(f'<polyline points="{pts}" fill="none" stroke="{colours[leg.force]}" stroke-width="2.4" '
                   f'stroke-opacity="0.85"{dash} marker-end="url(#arr{index[leg.force]})"/>')
    for loc in plan.locations.values():
        if loc.kind != "entity":
            continue
        side = SIDE.get(loc.side, "#333")
        if loc.footprint:
            h = loc.footprint * s
            fill = STRUCTURE.get(loc.side, "#555")
            out.append(f'<rect x="{X(loc.x) - h}" y="{Y(loc.y) - h}" width="{2 * h}" height="{2 * h}" fill="{fill}" '
                       f'fill-opacity="0.8" stroke="#000"/>')
        else:
            out.append(f'<circle cx="{X(loc.x)}" cy="{Y(loc.y)}" r="5" fill="{side}" stroke="#fff" stroke-width="1.5"/>')
        right = loc.x > W * 0.66
        out.append(f'<text x="{X(loc.x) + (-8 if right else 8) - (loc.footprint * s if right else -loc.footprint * s)}" '
                   f'y="{Y(loc.y) - 7}" font-weight="600" text-anchor="{"end" if right else "start"}" '
                   f'paint-order="stroke" stroke="#fff" stroke-width="3">{html.escape(loc.name)} ({loc.x:g}, {loc.y:g})</text>')
    out.append('</g></g>')
    y = mh + 50
    out.append(f'<text x="10" y="{y}" font-weight="600">Legs (cells; dashed = air; ramps crossed)</text>')
    for leg in [l for l in plan.legs if l.status != "already_there"]:
        y += 20
        c = colours.get(leg.force, "#333")
        info = (f"{leg.force}: {leg.origin.replace('spawn:', 'spawn ')} → {leg.target}  "
                f"[{leg.status}{', %.1f' % leg.length if leg.length else ''}"
                f"{', ' + '/'.join(leg.ramps) if leg.ramps else ''}]  {leg.context}")
        out.append(f'<rect x="10" y="{y - 9}" width="14" height="4" fill="{c}"/>'
                   f'<text x="30" y="{y - 4}">{html.escape(info)}</text>')
    out.append('</svg>')
    return "\n".join(out)


def to_png(plan: RoutePlan, profile: MapProfile, path: Path) -> bool:
    """PNG through matplotlib when it is installed; False otherwise."""
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from matplotlib.colors import ListedColormap
        from matplotlib.patches import Circle, Rectangle
    except ImportError:
        return False
    W, H = profile.width, profile.height
    order = [VOID, RAMP, 1, 2, 3, 4]
    idx = {v: i for i, v in enumerate(order)}
    img = [[idx.get(profile.level[j][i], 0) for i in range(W)] for j in range(H)]
    fig, ax = plt.subplots(figsize=(11, 11 * H / W + 0.4), dpi=110)
    ax.imshow(img, origin="lower", extent=(0, W, 0, H), vmin=0, vmax=len(order) - 1,
              cmap=ListedColormap([TERRAIN[v] for v in order]))
    for bx, by, _n in profile.blockers:
        ax.plot(bx, by, "x", color="#555", ms=3, alpha=0.6)
    for r in profile.ramps:
        ax.annotate(r.rid, r.center, fontsize=8, color="#7a5c00", ha="center", va="center", weight="bold")
    colours = _colours(plan)
    labelled = set()
    for leg in plan.legs:
        if len(leg.path) < 2:
            continue
        xs, ys = [p[0] for p in leg.path], [p[1] for p in leg.path]
        lab = None if leg.force in labelled else leg.force
        labelled.add(leg.force)
        ax.plot(xs, ys, "--" if leg.air else "-", color=colours[leg.force], lw=2.2, alpha=0.85, label=lab)
        ax.annotate("", xy=(xs[-1], ys[-1]), xytext=(xs[-2], ys[-2]),
                    arrowprops=dict(arrowstyle="-|>", color=colours[leg.force], lw=1.5))
    for loc in plan.locations.values():
        if loc.kind == "region":
            ax.add_patch(Circle((loc.x, loc.y), loc.radius, fill=False, ls="--", lw=1.4, ec="#222"))
            ax.annotate(loc.name, (loc.x, loc.y + loc.radius + 0.6), ha="center", fontsize=8, weight="bold")
        elif loc.footprint:
            h = loc.footprint
            ax.add_patch(Rectangle((loc.x - h, loc.y - h), 2 * h, 2 * h, fc=STRUCTURE.get(loc.side, "#555"), ec="k", alpha=0.8))
            ax.annotate(f"{loc.name}\n({loc.x:g}, {loc.y:g})", (loc.x, loc.y - h - 0.8), ha="center", va="top", fontsize=7)
        else:
            side = SIDE.get(loc.side, "#333")
            ax.plot(loc.x, loc.y, "o", ms=9, mfc=side, mec="white", mew=1.5)
            right = loc.x > W * 0.66
            ax.annotate(f"{loc.name}\n({loc.x:g}, {loc.y:g})", (loc.x + (-1 if right else 1), loc.y + 0.8),
                        ha="right" if right else "left", fontsize=7, color=side, weight="bold")
    ax.set_xlim(0, W)
    ax.set_ylim(0, H)
    ax.grid(color="white", lw=0.4, alpha=0.5)
    ax.set_title(f"{plan.strategy} on {plan.map}: movement legs over terrain (dashed = air)")
    ax.legend(loc="upper left", fontsize=8, framealpha=0.9)
    ax.text(0.5, -0.045, "dark = void, sand = ramp, greens = cliff level 1/2/3; x = blocking doodad; R* = ramps; "
             "paths approximate the editor's pathing", ha="center", va="top", fontsize=7, transform=ax.transAxes)
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    return True


def guess_base_map(source: Path, maps_dir: Path) -> Path:
    """The map a source is written for (same rule as tools/run_suite.py): cerulean_* -> cerulean_fall_le,
    arid_* -> arid_plateau, v04_* -> sdjx_te, <key>_* -> <key>_te when it exists, otherwise jctq_te."""
    stem = Path(source).stem
    if "cerulean" in stem:
        return maps_dir / "cerulean_fall_le.SC2Map"
    if stem.startswith("arid_"):
        return maps_dir / "arid_plateau.SC2Map"
    if stem.startswith("v04_"):
        return maps_dir / "sdjx_te.SC2Map"
    key = stem.split("_")[0]
    cand = maps_dir / f"{key}_te.SC2Map"
    return cand if cand.exists() else maps_dir / "jctq_te.SC2Map"


def write_routes(strategy: Strategy, base_map, out, stem: Optional[str] = None, *, png: bool = True,
                 profile: Optional[MapProfile] = None) -> tuple[RoutePlan, list[str]]:
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    stem = stem or strategy.name
    profile = profile or load_profile(base_map)
    plan = plan_routes(strategy, profile)
    files = [f"{stem}.routes.json", f"{stem}.routes.svg"]
    (out / files[0]).write_text(json.dumps(plan.to_dict(), ensure_ascii=False, indent=1), encoding="utf-8")
    (out / files[1]).write_text(to_svg(plan, profile), encoding="utf-8")
    if png and to_png(plan, profile, out / f"{stem}.routes.png"):
        files.append(f"{stem}.routes.png")
    return plan, files
