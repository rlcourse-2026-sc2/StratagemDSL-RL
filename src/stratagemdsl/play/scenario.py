"""What an agent plays with: the strategy's forces, assets and regions on the map."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from stratagemdsl.core.model import BindingCall, Strategy
from stratagemdsl.frontend.unparse import _print_expr
from stratagemdsl.packaging.terrain import MapProfile
from stratagemdsl.views.routes import AIR_UNITS, Location, resolve_locations

RACE_OF = {
    **dict.fromkeys(("Zealot", "Stalker", "Adept", "Sentry", "HighTemplar", "DarkTemplar", "Archon", "Immortal",
                     "Colossus", "Disruptor", "Observer", "WarpPrism", "Phoenix", "VoidRay", "Oracle", "Tempest",
                     "Carrier", "Mothership", "Probe", "Nexus", "Pylon", "Gateway", "PhotonCannon"), "protoss"),
    **dict.fromkeys(("Marine", "Marauder", "Reaper", "Ghost", "Hellion", "Hellbat", "SiegeTank", "Cyclone",
                     "WidowMine", "Thor", "VikingFighter", "Medivac", "Liberator", "Raven", "Banshee",
                     "Battlecruiser", "SCV", "CommandCenter", "OrbitalCommand", "Bunker", "MissileTurret",
                     "Barracks", "Factory", "Starport"), "terran"),
    **dict.fromkeys(("Zergling", "Baneling", "Roach", "Ravager", "Hydralisk", "Lurker", "Infestor", "SwarmHost",
                     "Ultralisk", "Mutalisk", "Corruptor", "BroodLord", "Viper", "Queen", "Overlord", "Overseer",
                     "Drone", "Hatchery", "Lair", "Hive", "SpineCrawler", "SporeCrawler"), "zerg"),
}
ACTIONS = ("move", "attack", "hold", "retreat")


@dataclass
class Force:
    name: str
    kind: str                 # force | asset
    side: str                 # ally | enemy | ""
    owner: Optional[int]
    unit_types: list[str]
    count: int                # units bound (0 when unknown)
    spawn: Optional[tuple[float, float]]
    role: str = ""
    composition: list[tuple[str, int]] = field(default_factory=list)   # (unit type, count)

    @property
    def air(self) -> bool:
        return bool(self.unit_types) and all(t in AIR_UNITS for t in self.unit_types)


@dataclass
class Scenario:
    strategy: Strategy
    profile: MapProfile
    forces: dict[str, Force]
    regions: dict[str, Location]
    objective: dict = field(default_factory=dict)   # success / failure as DSL text

    @property
    def controlled(self) -> list[str]:
        """Allied forces an agent gives orders to (assets do not move)."""
        return [f.name for f in self.forces.values() if f.side == "ally" and f.kind == "force"]

    @property
    def ally_owner(self) -> int:
        return next((f.owner for f in self.forces.values() if f.side == "ally" and f.owner), 1)

    def race(self, side: str) -> str:
        votes: dict[str, int] = {}
        for f in self.forces.values():
            if f.side == side:
                for t in f.unit_types:
                    if t in RACE_OF:
                        votes[RACE_OF[t]] = votes.get(RACE_OF[t], 0) + 1
        return max(votes, key=votes.get) if votes else "random"

    def targets(self, action: str) -> list[str]:
        """Names an action may take as its target."""
        if action in ("move", "retreat"):
            return sorted(self.regions)
        if action == "attack":
            return sorted([f.name for f in self.forces.values() if f.side == "enemy"] + list(self.regions))
        return []

    def vocabulary(self) -> str:
        lines = [f"Forces you command: {', '.join(self.controlled)}"]
        lines.append(f"  move(force, region)     walk to a region; units do not stop to fight on the way: "
                     f"{', '.join(self.targets('move')) or '-'}")
        lines.append(f"  attack(force, target)   attack-move: fight whatever is met on the way to an enemy force, "
                     f"structure or region: {', '.join(self.targets('attack')) or '-'}")
        lines.append("  hold(force)             stop and hold position (still fights in range)")
        lines.append("  retreat(force, region)  the same command as move; use it to pull a force back")
        return "\n".join(lines)


def _arg(call: BindingCall, name: str):
    return next((a.value for a in call.args if a.name == name), None)


def build_scenario(strategy: Strategy, profile: MapProfile) -> Scenario:
    locs, types = resolve_locations(strategy, profile)
    kinds = {e.name: e for e in strategy.world}
    forces: dict[str, Force] = {}
    for b in strategy.bindings:
        e = kinds.get(b.name)
        if e is None or e.kind not in ("force", "asset") or not isinstance(b.value, BindingCall):
            continue
        v = b.value
        owner = _arg(v, "owner")
        comp = [(str(_arg(c, "unit_type")), int(_arg(c, "count") or 1))
                for c in (_arg(v, "composition") or []) if isinstance(c, BindingCall) and _arg(c, "unit_type")]
        if not comp and isinstance(_arg(v, "unit_type"), str):
            comp = [(_arg(v, "unit_type"), int(_arg(v, "count") or 1))]
        count = sum(n for _, n in comp)
        loc = locs.get(b.name)
        forces[b.name] = Force(b.name, e.kind, str(e.properties.get("side", "")).strip('"'),
                               int(owner) if isinstance(owner, (int, float)) else None, types.get(b.name, []),
                               int(count), (loc.x, loc.y) if loc else None,
                               str(e.properties.get("role", "")).strip('"'), comp)
    regions = {n: l for n, l in locs.items() if l.kind == "region"}
    objective = {}
    if strategy.intent is not None:
        objective = {"success": _print_expr(strategy.intent.success), "failure": _print_expr(strategy.intent.failure)}
    return Scenario(strategy, profile, forces, regions, objective)
