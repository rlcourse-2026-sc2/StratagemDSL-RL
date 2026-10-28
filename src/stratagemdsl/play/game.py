"""Backend-neutral game state: what PySC2 (or the toy simulator) reports, what agents order.

Coordinates are always world coordinates of the map (x right, y up, cells),
the same as point_xy in the DSL; backends convert to their own frame.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Protocol

LOOPS_PER_SECOND = 22.4      # game loops per second at "faster" speed


@dataclass
class Unit:
    tag: int
    unit_type: str
    owner: int
    x: float
    y: float
    health: float
    shield: float = 0.0
    health_ratio: float = 1.0     # 0..1 of max health
    structure: bool = False


@dataclass
class Frame:
    game_loop: int
    units: list[Unit]
    player_id: int = 1
    done: bool = False
    result: Optional[str] = None      # victory | defeat | tie | timeout (when done)

    @property
    def seconds(self) -> float:
        return self.game_loop / LOOPS_PER_SECOND


@dataclass
class Order:
    kind: str                          # move | attack_pt | attack_unit | hold
    tags: list[int]
    point: Optional[tuple[float, float]] = None
    target_tag: Optional[int] = None
    meta: dict = field(default_factory=dict)   # the macro action it came from (for logs)


class Backend(Protocol):
    def reset(self) -> Frame: ...
    def step(self, orders: list[Order]) -> Frame: ...
    def close(self) -> None: ...
