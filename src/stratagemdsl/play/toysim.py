"""A movement-only stand-in for StarCraft II: tests and `strat play --dry-run`.

Units appear at their bindings' spawn points and walk in a straight line
toward their last order at a fixed speed; there is no combat, no pathing and
no map script. It exercises the whole agent loop -- unit matching, prompts,
LLM answers, orders, logs -- without the game. An optional `rule` decides
the result (e.g. "victory once raid_force enters enemy_home_zone").
"""
from __future__ import annotations

import math
from typing import Callable, Optional

from stratagemdsl.play.game import Frame, Order, Unit
from stratagemdsl.play.scenario import Scenario
from stratagemdsl.views.routes import FOOTPRINT

STEP_LOOPS = 8          # PySC2's default step_mul


class ToySim:
    def __init__(self, scenario: Scenario, *, speed: float = 3.0, max_loops: int = 22 * 60 * 10,
                 player_id: Optional[int] = None, rule: Optional[Callable[[Frame], Optional[str]]] = None):
        self.sc = scenario
        self.speed = speed               # cells per second
        self.max_loops = max_loops
        self.player_id = player_id or scenario.ally_owner
        self.rule = rule
        self.steps = 0

    def reset(self) -> Frame:
        self.loop, self.units, self.goal, tag = 0, [], {}, 1000
        for f in self.sc.forces.values():
            if f.spawn is None or f.owner is None:
                continue
            k = 0
            for t, n in (f.composition or [("Marine", max(1, f.count))]):
                for _ in range(n if f.kind == "force" else 1):
                    k += 1
                    ang = 2.39996 * k
                    r = 0.0 if f.kind == "asset" else 0.6 * math.sqrt(k)
                    self.units.append(Unit(tag, t, f.owner, f.spawn[0] + r * math.cos(ang),
                                           f.spawn[1] + r * math.sin(ang), 100.0,
                                           structure=t in FOOTPRINT))
                    tag += 1
        return self._frame()

    def step(self, orders: list[Order]) -> Frame:
        self.steps += 1
        by_tag = {u.tag: u for u in self.units}
        for o in orders:
            for t in o.tags:
                if o.kind == "hold":
                    self.goal.pop(t, None)
                elif o.kind == "attack_unit" and o.target_tag in by_tag:
                    tgt = by_tag[o.target_tag]
                    self.goal[t] = (tgt.x, tgt.y)
                elif o.point is not None:
                    self.goal[t] = o.point
        dt = STEP_LOOPS / 22.4
        for u in self.units:
            g = self.goal.get(u.tag)
            if g is None or u.structure:
                continue
            dx, dy = g[0] - u.x, g[1] - u.y
            d = math.hypot(dx, dy)
            k = min(1.0, self.speed * dt / d) if d > 1e-9 else 0.0
            u.x, u.y = u.x + dx * k, u.y + dy * k
        self.loop += STEP_LOOPS
        return self._frame()

    def _frame(self) -> Frame:
        f = Frame(self.loop, [Unit(**vars(u)) for u in self.units], self.player_id)
        result = self.rule(f) if self.rule else None
        if result is None and self.loop >= self.max_loops:
            result = "timeout"
        if result is not None:
            f.done, f.result = True, result
        return f

    def close(self) -> None:
        pass
