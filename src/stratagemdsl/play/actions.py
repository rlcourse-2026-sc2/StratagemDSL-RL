"""Macro actions in the DSL's vocabulary, checked against the scenario and turned into orders."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Optional

from stratagemdsl.play.game import Order
from stratagemdsl.play.observe import ForceTracker
from stratagemdsl.play.scenario import ACTIONS, Scenario


@dataclass
class MacroAction:
    force: str
    action: str
    target: Optional[str] = None

    def text(self) -> str:
        return f"{self.action}({self.force}{', ' + self.target if self.target else ''})"

    def to_dict(self) -> dict:
        return {k: v for k, v in asdict(self).items() if v is not None}


def parse_actions(items, scenario: Scenario) -> tuple[list[MacroAction], list[str]]:
    """Validate a list of {"force", "action", "target"} objects; returns (actions, errors)."""
    if not isinstance(items, list):
        return [], ["'orders' must be a list"]
    out, errors = [], []
    for i, item in enumerate(items):
        if not isinstance(item, dict):
            errors.append(f"order {i}: not an object")
            continue
        force, action, target = item.get("force"), str(item.get("action", "")).lower(), item.get("target")
        if force not in scenario.controlled:
            errors.append(f"order {i}: '{force}' is not a force you command ({', '.join(scenario.controlled)})")
            continue
        if action not in ACTIONS:
            errors.append(f"order {i}: unknown action '{action}' (use {', '.join(ACTIONS)})")
            continue
        if action == "hold":
            out.append(MacroAction(force, action))
            continue
        allowed = scenario.targets(action)
        if target not in allowed:
            errors.append(f"order {i}: {action} needs a target from: {', '.join(allowed)} (got '{target}')")
            continue
        out.append(MacroAction(force, action, target))
    return out, errors


def to_orders(actions: list[MacroAction], scenario: Scenario, tracker: ForceTracker) -> tuple[list[Order], list[str]]:
    """Orders for the force's living units; a force with no units left gives a note, not an order."""
    orders, notes = [], []
    for a in actions:
        tags = tracker.tags(a.force)
        if not tags:
            notes.append(f"{a.text()}: {a.force} has no units")
            continue
        meta = a.to_dict()
        if a.action == "hold":
            orders.append(Order("hold", tags, meta=meta))
            continue
        if a.target in scenario.regions:
            loc = scenario.regions[a.target]
            point = (loc.x, loc.y)
            kind = "attack_pt" if a.action == "attack" else "move"
            orders.append(Order(kind, tags, point=point, meta=meta))
            continue
        # an enemy force or structure
        st = tracker.states[a.target]
        f = scenario.forces[a.target]
        if f.kind == "asset" and len(st.alive) == 1:
            orders.append(Order("attack_unit", tags, target_tag=st.alive[0].tag, meta=meta))
            continue
        point = tracker.position(a.target)
        if point is None:
            notes.append(f"{a.text()}: no known position for {a.target}")
            continue
        orders.append(Order("attack_pt", tags, point=point, meta=meta))
    return orders, notes
