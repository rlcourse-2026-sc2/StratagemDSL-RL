"""The task bundle LLM-PySC2 reads to play a map built from a strategy (`strat llm-pysc2`).

LLM-PySC2 drives units through PySC2's feature-layer interface: its LLM
agents see units on the screen (tags, screen pixels) and move with
`Move_Minimap([x, y])` in minimap pixels. A generated map, on the other
hand, is described in the DSL's world cells (x right, y up). The bundle is
the contract between the two projects and carries both:

    map          the packed .SC2Map (built with --gameover) and its size
    interface    feature screen/minimap sizes and the camera width the
                 coordinates below were computed for
    races        allied / enemy race (LLM-PySC2 picks the action space)
    forces       every force/asset: side, owner, composition, spawn
                 (world and minimap), whether an agent commands it
    regions      named regions: centre and radius in world and minimap units
    objective    the intent's success / failure conditions as DSL text
    plan         the plan in words (phases, orders, what advances them);
                 per allied force the orders the plan gives it
    terrain      plateaus and ramps, in world and minimap coordinates
    source       the .strat file, so the bridge can follow the plan live

Minimap pixels follow PySC2 with `crop_to_playable_area=False`: the whole
map scaled by `minimap / max(width, height)`, origin top-left, y down.
"""
from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Optional

from stratagemdsl.core.model import Phase, Strategy
from stratagemdsl.frontend.unparse import _print_expr
from stratagemdsl.packaging.terrain import MapProfile
from stratagemdsl.play.agents import plan_brief, terrain_brief
from stratagemdsl.play.scenario import Scenario, build_scenario

FORMAT = "stratagemdsl.llm-pysc2-task.v1"
SCREEN, MINIMAP, CAMERA_WIDTH = 128, 64, 24
ALLY_ACTIONS = ("move", "attack", "hold", "retreat", "retarget", "cast", "set_mode", "block")


class Projection:
    """World cells <-> PySC2 feature-minimap pixels for one map."""

    def __init__(self, width: int, height: int, minimap: int = MINIMAP):
        self.width, self.height, self.minimap = width, height, minimap
        self.scale = minimap / max(width, height)

    def to_minimap(self, x: float, y: float) -> list[int]:
        mx = min(self.minimap - 1, max(0, int(math.floor(x * self.scale))))
        my = min(self.minimap - 1, max(0, int(math.floor((self.height - y) * self.scale))))
        return [mx, my]

    def to_world(self, mx: float, my: float) -> list[float]:
        return [round((mx + 0.5) / self.scale, 1), round(self.height - (my + 0.5) / self.scale, 1)]

    def length(self, cells: float) -> float:
        return round(cells * self.scale, 1)


def _phase_orders(strategy: Strategy, side: dict[str, str]):
    """(phase id, phase, [(force, call text, action, target)]) for phases with allied orders."""
    out = []
    for n in strategy.plan.nodes:
        if not isinstance(n, Phase) or n.terminal or not n.actions:
            continue
        items = []
        for call in n.actions.actions:
            if not call.args:
                continue
            actor = getattr(call.args[0], "name", None)
            target = getattr(call.args[1], "name", None) if len(call.args) > 1 else None
            if side.get(actor) == "ally":
                items.append((actor, _print_expr(call), call.name, target))
        if items:
            out.append((n.id, n, items))
    return out


def _entry_conditions(strategy: Strategy) -> dict[str, list[str]]:
    """phase id -> the transitions that put a token into it, in words."""
    out: dict[str, list[str]] = {}
    for t in strategy.plan.transitions:
        cond = []
        if t.event is not None:
            cond.append(f"on {_print_expr(t.event)}")
        if t.guard is not None:
            cond.append(f"when {_print_expr(t.guard)}")
        reads = [a.place for a in t.inputs if a.kind == "read"]
        if reads:
            cond.append("once " + ", ".join(reads) + " is marked")
        src = ", ".join(a.place for a in t.inputs if a.kind == "normal") or "-"
        for a in t.outputs:
            out.setdefault(a.place, []).append(f"after {src} {' '.join(cond)}".strip())
    return out


def force_plans(strategy: Strategy, scenario: Scenario, proj: Projection) -> dict[str, list[dict]]:
    side = {f.name: f.side for f in scenario.forces.values()}
    entry = _entry_conditions(strategy)
    start = set(strategy.plan.start)
    plans: dict[str, list[dict]] = {name: [] for name in scenario.controlled}
    for pid, ph, items in _phase_orders(strategy, side):
        for actor, text, action, target in items:
            if actor not in plans:
                continue
            step = {"phase": pid, "purpose": ph.purpose, "order": text, "action": action, "target": target,
                    "starts": "at the start" if pid in start else "; or ".join(entry.get(pid, [])) or "-"}
            if target in scenario.regions:
                r = scenario.regions[target]
                step["target_minimap"] = proj.to_minimap(r.x, r.y)
                step["target_world"] = [r.x, r.y]
            elif target in scenario.forces and scenario.forces[target].spawn:
                sx, sy = scenario.forces[target].spawn
                step["target_minimap"] = proj.to_minimap(sx, sy)
                step["target_world"] = [sx, sy]
                step["target_is"] = "moving force" if scenario.forces[target].kind == "force" else "structure"
            plans[actor].append(step)
    return plans


def terrain_minimap(profile: MapProfile, proj: Projection) -> str:
    lines = [f"Terrain in minimap pixels (0..{proj.minimap - 1}, x right, y DOWN; 1 pixel = "
             f"{1 / proj.scale:.2f} cells). Ground units change level only through ramps.",
             "Plateaus:"]
    for rg in profile.regions:
        x0, y0, x1, y1 = rg.bbox
        a, b = proj.to_minimap(x0, y1 + 1), proj.to_minimap(x1 + 1, y0)
        lines.append(f"  {rg.rid}: level {rg.level}, minimap x {a[0]}..{b[0]}, y {a[1]}..{b[1]}, "
                     f"ramps {', '.join(rg.ramps) or 'none'}")
    lines.append("Ramps:")
    lines += [f"  {rp.rid}: minimap {proj.to_minimap(*rp.center)}, joins {' and '.join(rp.joins)}"
              for rp in profile.ramps]
    return "\n".join(lines)


def build_bundle(strategy: Strategy, profile: MapProfile, map_path: Path, *, source: Optional[Path] = None,
                 scenario: Optional[Scenario] = None, gameover: bool = True, oracle: bool = False,
                 screen: int = SCREEN, minimap: int = MINIMAP, camera_width: int = CAMERA_WIDTH) -> dict:
    sc = scenario or build_scenario(strategy, profile)
    proj = Projection(profile.width, profile.height, minimap)
    forces = []
    for f in sc.forces.values():
        item = {"name": f.name, "kind": f.kind, "side": f.side, "owner": f.owner, "role": f.role,
                "unit_types": f.unit_types, "composition": [[t, n] for t, n in f.composition], "count": f.count,
                "air": f.air, "controlled": f.name in sc.controlled}
        if f.spawn:
            item["spawn"] = {"world": [f.spawn[0], f.spawn[1]], "minimap": proj.to_minimap(*f.spawn)}
        forces.append(item)
    roles = {e.name: str(e.properties.get("role", "")).strip('"') for e in strategy.world}
    regions = [{"name": n, "role": roles.get(n, ""), "world": [r.x, r.y], "radius": r.radius,
                "minimap": proj.to_minimap(r.x, r.y), "minimap_radius": proj.length(r.radius)}
               for n, r in sorted(sc.regions.items())]
    side = {f.name: f.side for f in sc.forces.values()}
    phases = []
    for n in strategy.plan.nodes:
        if isinstance(n, Phase):
            phases.append({"id": n.id, "purpose": n.purpose, "actors": list(n.actors), "terminal": n.terminal,
                           "orders": [_print_expr(a) for a in (n.actions.actions if n.actions else [])],
                           "ally_actors": [a for a in n.actors if side.get(a) == "ally"]})
    transitions = []
    for t in strategy.plan.transitions:
        transitions.append({"id": t.id, "inputs": [[a.place, a.kind] for a in t.inputs],
                            "outputs": [a.place for a in t.outputs],
                            "event": _print_expr(t.event) if t.event is not None else None,
                            "guard": _print_expr(t.guard) if t.guard is not None else None,
                            "actions": [_print_expr(a) for a in (t.actions.actions if t.actions else [])]})
    return {
        "format": FORMAT,
        "strategy": strategy.name,
        "source": str(Path(source).resolve()) if source else None,
        "map": {"path": str(Path(map_path).resolve()), "name": Path(map_path).stem, "base_map": profile.path.name,
                "width": profile.width, "height": profile.height, "bounds": list(profile.bounds),
                "gameover": gameover, "oracle": oracle},
        "interface": {"screen": screen, "minimap": minimap, "camera_width": camera_width,
                      "raw_resolution": max(profile.width, profile.height),
                      "minimap_scale": round(proj.scale, 6),
                      "coordinates": "world: cells, x right, y up (DSL point_xy); minimap: PySC2 feature-minimap "
                                     "pixels, x right, y down, world * minimap/max(width, height)"},
        "players": {"ally": sc.ally_owner, "enemy": next((f.owner for f in sc.forces.values()
                                                          if f.side == "enemy" and f.owner), 2)},
        "races": {"ally": sc.race("ally"), "enemy": sc.race("enemy")},
        "objective": sc.objective,
        "forces": forces,
        "regions": regions,
        "plan": {"start": list(strategy.plan.start), "phases": phases, "transitions": transitions,
                 "brief": plan_brief(sc), "force_plans": force_plans(strategy, sc, proj)},
        "terrain": {"world": terrain_brief(sc, False), "minimap": terrain_minimap(profile, proj)},
    }


def write_bundle(bundle: dict, out_dir: Path, stem: str) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{stem}.llm_pysc2.json"
    path.write_text(json.dumps(bundle, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path
