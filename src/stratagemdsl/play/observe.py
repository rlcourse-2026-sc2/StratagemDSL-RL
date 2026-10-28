"""Which unit belongs to which force, and the observation an LLM agent reads.

Units are matched to forces once, when they are first seen: same owner, a unit
type the binding lists, the nearest spawn point (assets: the structure at its
`at` point), and no more units than the binding spawns while another candidate
still has room. After that a unit keeps its force by tag.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Optional

from stratagemdsl.play.game import Frame, Unit
from stratagemdsl.play.scenario import Scenario

UNASSIGNED = "(other)"


@dataclass
class ForceState:
    name: str
    alive: list[Unit] = field(default_factory=list)
    seen: bool = False
    initial_units: int = 0
    initial_hp: float = 0.0
    last_seen: Optional[tuple[float, float]] = None
    last_seen_loop: int = -1
    regions: set[str] = field(default_factory=set)

    @property
    def centroid(self) -> Optional[tuple[float, float]]:
        if not self.alive:
            return None
        return (sum(u.x for u in self.alive) / len(self.alive), sum(u.y for u in self.alive) / len(self.alive))

    @property
    def hp(self) -> float:
        return sum(u.health + u.shield for u in self.alive)


class ForceTracker:
    def __init__(self, scenario: Scenario, player_id: int = 1):
        self.sc = scenario
        self.player_id = player_id
        self.force_of: dict[int, str] = {}
        self.states = {name: ForceState(name) for name in scenario.forces}
        self.events: list[dict] = []          # enter / leave / destroyed, with game loop
        self.calibration: dict[str, float] = {}   # force -> distance of first sighting from its spawn
        self._destroyed: set[str] = set()

    # ------------------------------------------------------------ matching
    def _candidates(self, u: Unit) -> list[str]:
        out = []
        for f in self.sc.forces.values():
            if f.owner is not None and f.owner != u.owner:
                continue
            if f.unit_types and u.unit_type not in f.unit_types:
                continue
            out.append(f.name)
        return out

    def _assign_new(self, units: list[Unit]) -> None:
        pairs = []
        for u in units:
            for name in self._candidates(u):
                f = self.sc.forces[name]
                ref = self.states[name].centroid or f.spawn
                d = math.hypot(u.x - ref[0], u.y - ref[1]) if ref else 1e9
                pairs.append((d, u.tag, name))
        pairs.sort()
        load = {n: sum(1 for v in self.force_of.values() if v == n) for n in self.sc.forces}
        done: set[int] = set()
        for overflow in (False, True):
            for d, tag, name in pairs:
                if tag in done:
                    continue
                cap = self.sc.forces[name].count
                if not overflow and cap and load[name] >= cap:
                    continue
                self.force_of[tag] = name
                load[name] += 1
                done.add(tag)
        for u in units:
            self.force_of.setdefault(u.tag, UNASSIGNED)

    # ------------------------------------------------------------- update
    def update(self, frame: Frame) -> None:
        self.player_id = frame.player_id
        new = [u for u in frame.units if u.tag not in self.force_of]
        if new:
            self._assign_new(new)
        for st in self.states.values():
            st.alive = []
        for u in frame.units:
            name = self.force_of.get(u.tag)
            if name in self.states:
                self.states[name].alive.append(u)
        for name, st in self.states.items():
            c = st.centroid
            if c is not None:
                if not st.seen:
                    st.seen = True
                    spawn = self.sc.forces[name].spawn
                    if spawn:
                        self.calibration[name] = round(math.hypot(c[0] - spawn[0], c[1] - spawn[1]), 2)
                # units may appear over several frames; enemies are seen in parts
                st.initial_units, st.initial_hp = max(st.initial_units, len(st.alive)), max(st.initial_hp, st.hp)
                st.last_seen, st.last_seen_loop = c, frame.game_loop
                if self.sc.forces[name].kind == "asset":
                    continue          # structures do not move: no enter/leave events
                inside = {r for r, loc in self.sc.regions.items()
                          if any(math.hypot(u.x - loc.x, u.y - loc.y) <= loc.radius for u in st.alive)}
                for r in sorted(inside - st.regions):
                    self.events.append({"loop": frame.game_loop, "event": "enter", "force": name, "region": r})
                for r in sorted(st.regions - inside):
                    self.events.append({"loop": frame.game_loop, "event": "leave", "force": name, "region": r})
                st.regions = inside
            elif st.seen and name not in self._destroyed and self._is_own(name):
                self._destroyed.add(name)
                self.events.append({"loop": frame.game_loop, "event": "destroyed", "force": name})

    def _is_own(self, name: str) -> bool:
        return self.sc.forces[name].owner == self.player_id

    # -------------------------------------------------------------- queries
    def tags(self, force: str) -> list[int]:
        return [u.tag for u in self.states[force].alive]

    def position(self, name: str) -> Optional[tuple[float, float]]:
        """Where a force or asset is (visible centroid, else last seen, else spawn)."""
        st = self.states.get(name)
        if st is None:
            return None
        return st.centroid or st.last_seen or self.sc.forces[name].spawn

    def calibration_problem(self, tolerance: float = 8.0) -> Optional[str]:
        """Units far from where the map spawned them = a coordinate frame mismatch."""
        far = {n: d for n, d in self.calibration.items() if d > tolerance}
        if far and len(far) * 2 >= len(self.calibration):
            return ("units were first seen far from their spawn points "
                    + ", ".join(f"{n} {d:g} cells" for n, d in sorted(far.items()))
                    + "; check the backend's coordinate transform")
        return None

    # ----------------------------------------------------------- reporting
    def summary(self) -> dict:
        out = {}
        for name, st in self.states.items():
            c = st.centroid
            out[name] = {"alive": len(st.alive), "initial": st.initial_units,
                         "hp": round(st.hp / st.initial_hp, 3) if st.initial_hp else None,
                         "at": [round(c[0], 1), round(c[1], 1)] if c else None,
                         "regions": sorted(st.regions)}
        return out

    def describe(self, frame: Frame) -> str:
        """The observation text for an LLM agent."""
        mm, ss = divmod(int(frame.seconds), 60)
        lines = [f"Game time {mm:02d}:{ss:02d} (loop {frame.game_loop})."]
        for title, side in (("Your forces and structures", "ally"), ("Enemy (only what you can see)", "enemy")):
            lines.append(f"{title}:")
            for name, f in self.sc.forces.items():
                if f.side != side:
                    continue
                lines.append("- " + self._describe_force(name, frame))
        return "\n".join(lines)

    def _describe_force(self, name: str, frame: Frame) -> str:
        f, st = self.sc.forces[name], self.states[name]
        if not st.alive:
            if not st.seen:
                where = f" (expected near ({f.spawn[0]:g}, {f.spawn[1]:g}))" if f.spawn else ""
                return f"{name}: not seen yet{where}"
            if self._is_own(name):
                return f"{name}: destroyed"
            secs = (frame.game_loop - st.last_seen_loop) / 22.4
            x, y = st.last_seen
            return f"{name}: not visible; last seen at ({x:.0f}, {y:.0f}) {secs:.0f} s ago"
        counts: dict[str, int] = {}
        for u in st.alive:
            counts[u.unit_type] = counts.get(u.unit_type, 0) + 1
        kinds = ", ".join(f"{n} {t}" for t, n in sorted(counts.items()))
        x, y = st.centroid
        plateau = self.sc.profile.region_at(x, y) or "-"
        hp = f", HP+shields {100 * st.hp / st.initial_hp:.0f}%" if st.initial_hp else ""
        size = f"{len(st.alive)}/{st.initial_units} alive" if self._is_own(name) else f"{len(st.alive)} visible"
        regions = ", ".join(sorted(st.regions)) or "none"
        return f"{name}: {size} ({kinds}){hp}, at ({x:.0f}, {y:.0f}) on {plateau}; in regions: {regions}"
