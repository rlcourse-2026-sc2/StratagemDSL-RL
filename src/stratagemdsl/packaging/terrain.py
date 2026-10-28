"""Terrain profile of a base .SC2Map, for placing point_xy coordinates.

Reads the archive members every melee map has:

* ``MapInfo``          map size, tileset and the playable (camera) bounds
* ``t3SyncCliffLevel`` one cliff value per cell: 64 = level 1, 128 = level 2,
                       192 = level 3, other non-zero values are ramps, 0 is void
* ``Objects``          doodads (possible blockers) and existing points/units

``MapProfile.render_context()`` turns this into the text block the LLM prompt
uses; ``check_bindings()`` verifies every point in a strategy's sc2 binding.
Pathing is approximated from cliff levels and doodad positions only; the real
pathing map is computed by the editor and is not stored in the archive.
"""
from __future__ import annotations

import math
import re
import struct
import xml.etree.ElementTree as ET
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from stratagemdsl.core.model import BindingCall
from stratagemdsl.packaging.mpq import open_archive

VOID, RAMP = 0, -1
# Doodads whose names contain these words are decals or effects, not obstacles.
_DECORATIVE = ("logo", "rain", "sprinkle", "decal", "curtain", "fog", "light", "dust", "smoke", "glow", "shadow")
# Half side length of common structure footprints (Hatchery is 5 x 5 -> 2.5).
FOOTPRINT = {
    **dict.fromkeys(("Hatchery", "Lair", "Hive", "Nexus", "CommandCenter", "OrbitalCommand",
                     "PlanetaryFortress", "CommandCenterFlying"), 2.5),
    **dict.fromkeys(("Gateway", "WarpGate", "Barracks", "Factory", "Starport", "SpawningPool", "RoachWarren",
                     "Forge", "CyberneticsCore", "EvolutionChamber", "Bunker", "Assimilator", "Refinery",
                     "Extractor", "NydusNetwork", "TwilightCouncil", "Stargate", "RoboticsFacility",
                     "RoboticsBay", "FleetBeacon", "TemplarArchive", "DarkShrine", "EngineeringBay",
                     "Armory", "FusionCore", "GhostAcademy", "HydraliskDen", "BanelingNest", "Spire",
                     "InfestationPit", "UltraliskCavern", "LurkerDen", "SensorTower"), 1.5),
    **dict.fromkeys(("Pylon", "PhotonCannon", "ShieldBattery", "SpineCrawler", "SporeCrawler",
                     "MissileTurret", "SupplyDepot", "NydusCanal", "CreepTumor"), 1.0),
}
UNIT_SPAWN_RADIUS = 1.0


@dataclass
class Region:
    rid: str
    level: int
    cells: int
    bbox: tuple[int, int, int, int]       # x0, y0, x1, y1 (inclusive)
    open_point: tuple[float, float]       # cell farthest from any edge of the region
    ramps: list[str] = field(default_factory=list)


@dataclass
class Ramp:
    rid: str
    center: tuple[float, float]
    joins: list[str]


@dataclass
class MapProfile:
    path: Path
    width: int
    height: int
    tileset: str
    bounds: tuple[float, float, float, float]   # left, bottom, right, top (playable)
    level: list[list[int]]                      # level[y][x]: 0 void, -1 ramp, 1..n height level
    blockers: list[tuple[float, float, str]]
    points: list[tuple[float, float, str]]      # existing ObjectPoint / unit markers
    regions: list[Region] = field(default_factory=list)
    ramps: list[Ramp] = field(default_factory=list)
    point_ids: dict = field(default_factory=dict)  # ObjectPoint Id -> (x, y), resolves point_id(...)
    _region_of: dict = field(default_factory=dict, repr=False)

    # ------------------------------------------------------------ cell queries
    def in_bounds(self, x: float, y: float) -> bool:
        l, b, r, t = self.bounds
        return l <= x < r and b <= y < t

    def cell(self, x: float, y: float) -> Optional[int]:
        i, j = int(math.floor(x)), int(math.floor(y))
        if not (0 <= i < self.width and 0 <= j < self.height) or not self.in_bounds(i + 0.5, j + 0.5):
            return None
        return self.level[j][i]

    def walkable(self, x: float, y: float) -> bool:
        v = self.cell(x, y)
        return v is not None and v != VOID

    def _cells_within(self, x: float, y: float, half: float):
        for j in range(int(math.floor(y - half)), int(math.ceil(y + half))):
            for i in range(int(math.floor(x - half)), int(math.ceil(x + half))):
                yield i + 0.5, j + 0.5

    def region_at(self, x: float, y: float) -> Optional[str]:
        return self._region_of.get((int(math.floor(x)), int(math.floor(y))))

    # ------------------------------------------------------------ point checks
    def check_point(self, x: float, y: float, *, structure_half: float = 0.0, what: str = "point") -> list[str]:
        """Problems with placing something at (x, y); empty list when fine."""
        if not self.in_bounds(x, y):
            l, b, r, t = self.bounds
            return [f"{what} ({x:g}, {y:g}) is outside the playable area x {l:g}..{r:g}, y {b:g}..{t:g}"]
        if structure_half:
            levels = {self.cell(cx, cy) for cx, cy in self._cells_within(x, y, structure_half)}
            if None in levels or VOID in levels:
                return [f"{what} footprint at ({x:g}, {y:g}) overlaps void/off-map cells"]
            if RAMP in levels:
                return [f"{what} footprint at ({x:g}, {y:g}) overlaps a ramp; structures need flat ground"]
            if len(levels) > 1:
                return [f"{what} footprint at ({x:g}, {y:g}) spans cliff levels {sorted(levels)}"]
            near = [b for b in self.blockers if abs(b[0] - x) < structure_half + 1 and abs(b[1] - y) < structure_half + 1]
            if near:
                return [f"{what} footprint at ({x:g}, {y:g}) overlaps doodad {near[0][2]} at ({near[0][0]:.1f}, {near[0][1]:.1f})"]
            return []
        if not self.walkable(x, y):
            return [f"{what} ({x:g}, {y:g}) is on a void/blocked cell"]
        return []

    def spawn_ok(self, x: float, y: float) -> bool:
        """A unit group needs walkable ground around its spawn point, not just under it."""
        ring = [(x + dx, y + dy) for dx in (-UNIT_SPAWN_RADIUS, 0, UNIT_SPAWN_RADIUS)
                for dy in (-UNIT_SPAWN_RADIUS, 0, UNIT_SPAWN_RADIUS)]
        return sum(self.walkable(px, py) for px, py in ring) >= 5

    def nearest_valid(self, x: float, y: float, *, structure_half: float = 0.0, spawn: bool = False,
                      max_radius: int = 24) -> Optional[tuple[float, float]]:
        """Closest spot to (x, y) that passes the same checks, preferring the same cliff level.

        Structure centres keep the footprint on whole cells (x.5 for odd sizes,
        integers for even ones); unit points use cell centres.
        """
        l, b, r, t = self.bounds
        cx = min(max(x, l + 0.5), r - 0.5)
        cy = min(max(y, b + 0.5), t - 0.5)
        want = self.cell(cx, cy)
        offset = 0.0 if structure_half and float(structure_half).is_integer() else 0.5
        best, best_score = None, None
        for j in range(int(cy) - max_radius, int(cy) + max_radius + 1):
            for i in range(int(cx) - max_radius, int(cx) + max_radius + 1):
                px, py = i + offset, j + offset
                d = math.hypot(px - cx, py - cy)
                if d > max_radius or (best_score is not None and d >= best_score):
                    continue
                if self.check_point(px, py, structure_half=structure_half):
                    continue
                if spawn and not structure_half and not self.spawn_ok(px, py):
                    continue
                score = d + (4.0 if want not in (None, VOID, RAMP) and self.cell(px, py) != want else 0.0)
                if best_score is None or score < best_score:
                    best, best_score = (px, py), score
        return best

    def describe_spot(self, x: float, y: float) -> str:
        v = self.cell(x, y)
        where = self.region_at(x, y)
        level = "ramp" if v == RAMP else f"level {v}"
        return f"point_xy({x:g}, {y:g})" + (f" on {where}, {level}" if where else f", {level}")

    def reachable(self, a: tuple[float, float], b: tuple[float, float]) -> bool:
        """Approximate ground connectivity: same level, or through a ramp cell."""
        start = (int(a[0]), int(a[1]))
        goal = (int(b[0]), int(b[1]))
        if self.cell(*a) in (None, VOID) or self.cell(*b) in (None, VOID):
            return False
        seen, queue = {start}, deque([start])
        while queue:
            u = queue.popleft()
            if u == goal:
                return True
            lu = self.level[u[1]][u[0]]
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                v = (u[0] + dx, u[1] + dy)
                if v in seen or self.cell(v[0] + 0.5, v[1] + 0.5) in (None, VOID):
                    continue
                lv = self.level[v[1]][v[0]]
                if lu == lv or RAMP in (lu, lv):
                    seen.add(v)
                    queue.append(v)
        return False

    # ------------------------------------------------------------ prompt text
    def render_grid(self, max_cols: int = 96) -> str:
        l, b, r, t = (int(math.floor(self.bounds[0])), int(math.floor(self.bounds[1])),
                      int(math.ceil(self.bounds[2])), int(math.ceil(self.bounds[3])))
        step = max(1, math.ceil((r - l) / max_cols))
        blocked = {(int(bx), int(by)) for bx, by, _ in self.blockers}
        rows = []
        for y in range(t - step, b - 1, -step):
            chars = []
            for x in range(l, r, step):
                block = [(x + i, y + j) for i in range(step) for j in range(step)
                         if x + i < self.width and y + j < self.height]
                vals = [self.level[cy][cx] for cx, cy in block]
                if any(c in blocked for c in block):
                    chars.append("x")
                elif VOID in vals:
                    chars.append("#")
                elif RAMP in vals:
                    chars.append("/")
                else:
                    chars.append(str(max(vals)))
            rows.append(f"{y:4d} {''.join(chars)}")
        axis = "".join(str((x // 10) % 10) if x % 10 == 0 else " " for x in range(l, r, step))
        rows.append("     " + axis)
        rows.append("     " + "".join(str(x % 10) for x in range(l, r, step)))
        return "\n".join(rows) + (f"\n(one character = {step} x {step} cells)" if step > 1 else "")

    def render_context(self) -> str:
        l, b, r, t = self.bounds
        lines = [
            f"Map: {self.path.name} ({self.width} x {self.height} cells, tileset {self.tileset})",
            f"Playable region: x {l:g}..{r:g}, y {b:g}..{t:g} (point_xy must lie inside; y grows upward)",
            "Grid legend: 1/2/3 = walkable ground at that cliff level (higher digit = higher ground);",
            "  '/' = ramp (walkable, joins two levels; no structures); '#' = void, impassable;",
            "  'x' = doodad that may block units or structures. Only digit cells are valid",
            "  for structures; keep structure centers at least 3 cells from a different symbol.",
            "Structure footprints (half size): Hatchery/Nexus/CommandCenter 2.5, production 1.5,",
            "  Pylon/cannons/crawlers 1.0. Unit groups need a walkable cell; they spread around it.",
            "",
            "Plateaus (connected ground at one level; open point = most interior cell):",
        ]
        for rg in self.regions:
            x0, y0, x1, y1 = rg.bbox
            lines.append(f"  {rg.rid}: level {rg.level}, {rg.cells} cells, x {x0}..{x1}, y {y0}..{y1}, "
                         f"open point ({rg.open_point[0]:g}, {rg.open_point[1]:g}), ramps {', '.join(rg.ramps) or 'none'}")
        lines.append("Ramps (walkable links between plateaus):")
        for rp in self.ramps:
            lines.append(f"  {rp.rid}: center ({rp.center[0]:g}, {rp.center[1]:g}) joins {' <-> '.join(rp.joins)}")
        if self.points:
            lines.append("Existing map markers (usable as point_xy anchors):")
            lines += [f"  {name} at ({px:.1f}, {py:.1f})" for px, py, name in self.points[:40]]
        lines += ["", "Terrain grid (rows from north to south):", self.render_grid()]
        return "\n".join(lines)


# ---------------------------------------------------------------- loading
def _parse_mapinfo(data: bytes) -> tuple[int, int, str, Optional[tuple[int, int, int, int]]]:
    width, height = struct.unpack_from("<II", data, 16)
    m = re.search(rb"([A-Za-z]+)\x00([A-Za-z0-9_]+)\x00", data[16:])
    if not m:
        return width, height, "", None
    end = 16 + m.end()
    left, bottom, right, top = struct.unpack_from("<IIII", data, end)
    bounds = (left, bottom, right, top) if 0 <= left < right <= width and 0 <= bottom < top <= height else None
    return width, height, m.group(2).decode(), bounds


def _parse_cliffs(data: bytes, width: int, height: int) -> list[list[int]]:
    offset = len(data) - width * height * 2
    raw = struct.unpack_from(f"<{width * height}H", data, offset)
    def level(v: int) -> int:
        if v == 0:
            return VOID
        return v // 64 if v % 64 == 0 else RAMP
    return [[level(raw[y * width + x]) for x in range(width)] for y in range(height)]


def _components(profile: MapProfile, predicate) -> list[list[tuple[int, int]]]:
    seen, comps = set(), []
    for y in range(profile.height):
        for x in range(profile.width):
            if (x, y) in seen or not predicate(x, y):
                continue
            comp, queue = [], deque([(x, y)])
            seen.add((x, y))
            while queue:
                u = queue.popleft()
                comp.append(u)
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    v = (u[0] + dx, u[1] + dy)
                    if v not in seen and 0 <= v[0] < profile.width and 0 <= v[1] < profile.height \
                            and predicate(*v) and profile.level[v[1]][v[0]] == profile.level[u[1]][u[0]]:
                        seen.add(v)
                        queue.append(v)
            comps.append(comp)
    return comps


def _analyse(profile: MapProfile, min_cells: int = 12) -> None:
    usable = lambda x, y: profile.cell(x + 0.5, y + 0.5) not in (None, VOID)
    flat = [c for c in _components(profile, lambda x, y: usable(x, y) and profile.level[y][x] > 0) if len(c) >= min_cells]
    flat.sort(key=lambda c: (-profile.level[c[0][1]][c[0][0]], -len(c)))
    blocked = {(int(bx), int(by)) for bx, by, _ in profile.blockers}
    for n, comp in enumerate(flat):
        cells = set(comp)
        # Distance from the region edge (and from blockers) by multi-source BFS.
        dist = {c: 0 for c in comp if c in blocked or any((c[0] + dx, c[1] + dy) not in cells
                                                         for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))}
        queue = deque(dist)
        while queue:
            u = queue.popleft()
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                v = (u[0] + dx, u[1] + dy)
                if v in cells and v not in dist:
                    dist[v] = dist[u] + 1
                    queue.append(v)
        best = max(comp, key=lambda c: (dist.get(c, 0), -c[1], -c[0]))
        xs, ys = [c[0] for c in comp], [c[1] for c in comp]
        rid = f"P{n + 1}"
        profile.regions.append(Region(rid, profile.level[comp[0][1]][comp[0][0]], len(comp),
                                      (min(xs), min(ys), max(xs), max(ys)), (best[0] + 0.5, best[1] + 0.5)))
        for c in comp:
            profile._region_of[c] = rid
    ramp_cells = [c for c in _components(profile, lambda x, y: usable(x, y) and profile.level[y][x] == RAMP) if len(c) >= 2]
    for n, comp in enumerate(ramp_cells):
        joins = sorted({profile._region_of[(c[0] + dx, c[1] + dy)] for c in comp for dx in (-2, -1, 0, 1, 2)
                        for dy in (-2, -1, 0, 1, 2) if (c[0] + dx, c[1] + dy) in profile._region_of})
        if len(joins) < 2:
            continue
        cx = sum(c[0] for c in comp) / len(comp) + 0.5
        cy = sum(c[1] for c in comp) / len(comp) + 0.5
        rid = f"R{len(profile.ramps) + 1}"
        profile.ramps.append(Ramp(rid, (round(cx, 1), round(cy, 1)), joins))
        for rg in profile.regions:
            if rg.rid in joins:
                rg.ramps.append(rid)


def load_profile(map_path: str | Path, stormlib: Optional[Path] = None) -> MapProfile:
    map_path = Path(map_path)
    with open_archive(map_path, library=stormlib) as archive:
        names = set(archive.names())
        width, height, tileset, bounds = _parse_mapinfo(archive.read("MapInfo"))
        level = _parse_cliffs(archive.read("t3SyncCliffLevel"), width, height) if "t3SyncCliffLevel" in names \
            else [[1] * width for _ in range(height)]
        objects = ET.fromstring(archive.read("Objects")) if "Objects" in names else ET.Element("PlacedObjects")
    blockers, points, point_ids = [], [], {}
    for obj in objects:
        pos = obj.get("Position")
        if not pos:
            continue
        px, py = (float(v) for v in pos.split(",")[:2])
        kind = obj.get("Type") or obj.get("UnitType") or ""
        if obj.tag == "ObjectDoodad":
            if not any(word in kind.lower() for word in _DECORATIVE):
                blockers.append((px, py, kind))
        elif obj.tag == "ObjectPoint":
            points.append((px, py, f"point {obj.get('Name') or obj.get('Id')}"))
            if (obj.get("Id") or "").isdigit():
                point_ids[int(obj.get("Id"))] = (px, py)
        elif obj.tag == "ObjectUnit":
            points.append((px, py, f"unit {kind} (player {obj.get('Player', '0')})"))
            blockers.append((px, py, kind))
    profile = MapProfile(map_path, width, height, tileset, bounds or (0, 0, width, height), level, blockers, points,
                         point_ids=point_ids)
    _analyse(profile)
    return profile


# ---------------------------------------------------------------- strategy checks
_PAIR = re.compile(r"\(\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*\)")


def brief_coordinate_problems(text: str, profile: MapProfile) -> list[str]:
    """Coordinates written in a designer brief that cannot be on this map.

    Usually they were copied from another map's `strat mapinfo` output.
    """
    problems = []
    for m in _PAIR.finditer(text):
        x, y = float(m.group(1)), float(m.group(2))
        if not profile.in_bounds(x, y):
            l, b, r, t = profile.bounds
            problems.append(f"({x:g}, {y:g}) is outside {profile.path.name} (x {l:g}..{r:g}, y {b:g}..{t:g})")
        elif not profile.walkable(x, y):
            problems.append(f"({x:g}, {y:g}) is void/impassable on {profile.path.name}")
    return problems



def _num(call: BindingCall, name: str, index: int):
    named = next((a.value for a in call.args if a.name == name), None)
    if named is not None:
        return named
    pos = [a.value for a in call.args if a.name is None]
    return pos[index] if index < len(pos) else None


def check_bindings(strategy, profile: MapProfile, *, allow_point_id: bool = False) -> list[str]:
    """Every point in the sc2 binding must land on usable terrain of this map."""
    problems: list[str] = []
    known_ids = set()

    def visit(value, owner: str, unit_type: Optional[str], role: str) -> None:
        if isinstance(value, list):
            for item in value:
                visit(item, owner, unit_type, role)
            return
        if not isinstance(value, BindingCall):
            return
        if value.name == "point_xy":
            x, y = _num(value, "x", 0), _num(value, "y", 1)
            if not isinstance(x, (int, float)) or not isinstance(y, (int, float)):
                problems.append(f"{owner}: point_xy needs two numbers")
                return
            half = FOOTPRINT.get(unit_type or "", 0.0) if role == "at" else 0.0
            what = f"{owner}.{role}" + (f" ({unit_type})" if unit_type else "")
            spawn = role == "spawn" and not half
            found = profile.check_point(float(x), float(y), structure_half=half, what=what)
            if spawn and not found and not profile.spawn_ok(float(x), float(y)):
                found = [f"{what} ({x:g}, {y:g}) has too little walkable ground around it for a unit group"]
            if found:
                # Hand the model a concrete fix instead of only the complaint.
                fix = profile.nearest_valid(float(x), float(y), structure_half=half, spawn=spawn)
                hint = f"; nearest valid spot: {profile.describe_spot(*fix)}" if fix else ""
                problems.extend(msg + hint for msg in found)
            return
        if value.name == "point_id":
            if not allow_point_id:
                problems.append(f"{owner}.{role}: point_id is not portable to {profile.path.name}; use point_xy(x, y)")
            return
        inner_type = next((a.value for a in value.args if a.name == "unit_type" and isinstance(a.value, str)), unit_type)
        for arg in value.args:
            visit(arg.value, owner, inner_type, arg.name or role)

    for binding in strategy.bindings:
        if binding.name != "__setup__":
            visit(binding.value, binding.name, None, "value")
    return problems
