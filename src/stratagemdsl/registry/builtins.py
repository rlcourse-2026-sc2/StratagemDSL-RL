from __future__ import annotations

from stratagemdsl.registry.contracts import Signature, signature_table


# Simple nominal type lattice for v0.2.
PARENT: dict[str, str | None] = {
    "Any": None,
    "Entity": "Any",
    "Force": "Entity",
    "Asset": "Entity",
    "Location": "Any",
    "Region": "Location",
    "Route": "Location",
    "Bool": "Any",
    "Int": "Any",
    "Float": "Any",
    "Number": "Any",
    "String": "Any",
}

ENTITY_KIND_TYPE = {
    "force": "Force",
    "asset": "Asset",
    "region": "Region",
    "route": "Route",
}

# These legacy exports remain usable, but their signatures have one owner.
FUNCTIONS: dict[str, list[Signature]] = signature_table("function")
EVENTS: dict[str, list[Signature]] = signature_table("event")
ACTIONS: dict[str, list[Signature]] = signature_table("action")


def is_subtype(actual: str, expected: str) -> bool:
    if expected == "Any":
        return True
    if actual == expected:
        return True
    if actual == "Int" and expected in {"Float", "Number"}:
        return True
    if actual == "Float" and expected == "Number":
        return True

    cur = actual
    seen: set[str] = set()
    while cur in PARENT and cur not in seen:
        seen.add(cur)
        cur = PARENT[cur]
        if cur == expected:
            return True
        if cur is None:
            break
    return False


# Interaction compatibility layer (v0.4 integration).
# Values are taken from the bundled historical Galaxy compiler symbol cache.
TARGET_FILTER_BITS = {'Self': 0, 'Player': 1, 'Ally': 2, 'Neutral': 3, 'Enemy': 4, 'Air': 5, 'Ground': 6, 'Light': 7, 'Armored': 8, 'Biological': 9, 'Robotic': 10, 'Mechanical': 11, 'Psionic': 12, 'Massive': 13, 'Structure': 14, 'Hover': 15, 'Heroic': 16, 'User1': 17, 'Worker': 18, 'RawResource': 19, 'HarvestableResource': 20, 'Missile': 21, 'Destructible': 22, 'Item': 23, 'Uncommandable': 24, 'CanHaveEnergy': 25, 'CanHaveShields': 26, 'PreventDefeat': 27, 'PreventReveal': 28, 'Buried': 29, 'Cloaked': 30, 'Visible': 31, 'Stasis': 32, 'UnderConstruction': 33, 'Dead': 34, 'Revivable': 35, 'Hidden': 36, 'Hallucination': 37, 'Invulnerable': 38, 'HasEnergy': 39, 'HasShields': 40, 'Benign': 41, 'Passive': 42, 'Detector': 43, 'Radar': 44, 'Stunned': 45, 'Summoned': 46, 'Unstoppable': 47, 'Outer': 48, 'Resistant': 49, 'Silenced': 50, 'Dazed': 51, 'MapBoss': 52, 'Decaying': 53, 'Raisable': 54, 'HeroUnit': 55, 'NonBuildingUnit': 56, 'GroundUnit': 57, 'AirUnit': 58, 'Powerup': 59, 'PowerupOrItem': 60, 'NeutralHostile': 61}
VISIBILITY_SIDES = {"ally": 1, "enemy": 2}
PHASE_ARGS = {"elapsed": (0,), "timer": (0,), "tokens": (0,), "active": (0,)}
EVENT_CONTEXT = {
    "event_source_in": frozenset({"unit_died", "unit_damaged", "effect_used"}),
    "event_target_in": frozenset({"unit_attacked", "effect_used"}),
    "event_amount": frozenset({"unit_damaged"}),
    "event_in": frozenset({"unit_died", "unit_damaged", "unit_attacked", "enter", "leave", "effect_used"}),
}

def parse_filter_spec(spec: str):
    """Return required names, excluded names and diagnostics; no implicit match-all."""
    required, excluded, errors = [], [], []
    for token in spec.split(","):
        token = token.strip()
        name = token[1:].strip() if token.startswith("-") else token
        if name not in TARGET_FILTER_BITS:
            errors.append(f"unknown target filter '{name}'")
        elif name in required or name in excluded:
            errors.append(f"filter '{name}' listed twice")
        else:
            (excluded if token.startswith("-") else required).append(name)
    return required, excluded, errors
