"""Canonical callable API contracts for StratagemDSL.

The registry owns the legal signatures and the *scope* of their SC2 evidence.
The checker and backend still make the final decision for a particular binding;
``backend='lowered'`` means a lowering rule exists, not that every map or unit
combination succeeds at runtime.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Literal


@dataclass(frozen=True)
class Signature:
    args: tuple[str, ...]
    returns: str


@dataclass(frozen=True)
class ApiSpec:
    name: str
    namespace: Literal["function", "event", "action"]
    signatures: tuple[Signature, ...]
    backend: Literal["lowered", "strategic_only", "unsupported", "special_context"]
    galaxy: str
    prerequisites: str
    issue_evidence: str
    effect_evidence: str
    actor: str = "none"
    alias_of: str = ""


def _entry(name, namespace, sigs, backend, galaxy, prerequisites="", issue="", effect="", actor="none", alias=""):
    signatures = tuple(Signature(tuple(args), result) for args, result in sigs)
    return ApiSpec(name, namespace, signatures, backend, galaxy, prerequisites, issue, effect, actor, alias)


# A function can be legal in a strategic intent without being available as a
# Galaxy transition guard. Each entry states this explicitly.
_ROWS = [
    _entry("alive", "function", [(('Entity',), 'Bool')], "lowered", "UnitGroupCount(group, alive)>0", "bound entity", effect="live group membership"),
    _entry("destroyed", "function", [(('Entity',), 'Bool')], "lowered", "UnitGroupCount(group, alive)==0", "bound entity", effect="no live group member"),
    _entry("defeated", "function", [(('Force',), 'Bool')], "lowered", "UnitGroupCount(group, alive)==0", "bound force", effect="no live group member"),
    _entry("relieved", "function", [(('Asset',), 'Bool')], "strategic_only", "none", "describe in intent/derive; ground a guard in observable state", effect="no automatic proof of relief"),
    _entry("at", "function", [(('Entity','Location'), 'Bool')], "unsupported", "none", "use in_region(force, circle) for a concrete guard"),
    _entry("in_region", "function", [(('Entity','Region'), 'Bool')], "lowered", "UnitGroupFilterRegion + UnitGroupCount > 0", "circle region and bound force/asset", effect="at least one live unit in region"),
    _entry("targeting", "function", [(('Force','Entity'), 'Bool')], "strategic_only", "none", "no target-state observer in backend", effect="no runtime targeting proof"),
    _entry("retargeted", "function", [(('Force','Entity'), 'Bool')], "strategic_only", "none", "retarget order does not prove retargeting", effect="no runtime retarget proof"),
    _entry("retreating", "function", [(('Force',), 'Bool')], "unsupported", "none", "no movement-state observer in backend"),
    _entry("threatened", "function", [(('Asset',), 'Bool')], "unsupported", "none", "no threat observer in backend"),
    _entry("defense_weakened", "function", [(('Asset',), 'Bool')], "strategic_only", "none", "pattern inference is plan evidence, not a runtime observation", effect="use count_in or other observable proof"),
    _entry("support_separated", "function", [(('Force','Entity'), 'Bool')], "unsupported", "none", "no separation observer in backend"),
    _entry("center_passable", "function", [(('Region',), 'Bool')], "lowered", "PointPathingPassable(region.center)", "circle region with a point center", effect="center point passable; does not prove route reachability"),
    _entry("path_passable", "function", [(('Region',), 'Bool')], "lowered", "PointPathingPassable(region.center)", "compatibility alias; prefer center_passable", effect="center point only, no path", alias="center_passable"),
    _entry("path_connected", "function", [(('Region','Region'), 'Bool')], "lowered", "PointPathingIsConnected(a.center, b.center)", "two circle regions with point centers; ground pathing only", effect="center-to-center ground connectivity, not unit-specific reachability"),
    _entry("creep_available", "function", [(('Region',), 'Bool')], "lowered", "CreepIsPresent(region.center)", "circle region with point center", effect="creep at center point"),
    _entry("construction_complete", "function", [(('Asset',), 'Bool')], "lowered", "live singleton group AND !libNtve_gf_UnitIsUnderConstruction(UnitGroupUnit(group,1))", "asset must bind one stable unit; returns false when dead", effect="current live unit is no longer under construction"),
    _entry("mode_is", "function", [(('Entity','String'), 'Bool')], "unsupported", "none", "ability order is not mode state"),
    _entry("count", "function", [(('Force',), 'Int')], "lowered", "UnitGroupCount(bound force, alive)", "bound force", effect="live units in this exact bound group"),
    _entry("count_in", "function", [(('Force','Region'), 'Int')], "lowered", "UnitGroupCount(UnitGroupFilterRegion(...), alive)", "bound force and circle", effect="live bound members in region"),
    _entry("killed_in", "function", [(('Force','Region'), 'Int')], "special_context", "unit_died monitor + deduplicated counter", "circle; in guards use a comparison such as killed_in(f,r)>=3", effect="cumulative deduplicated death count in region"),
    _entry("distance", "function", [(('Entity','Entity'), 'Float')], "lowered", "DistanceBetweenPoints(group center, group center)", "both live; strict guard requires explicit alive conjuncts", effect="distance of current group centers"),
    _entry("mission_time", "function", [((), 'Float')], "lowered", "GameGetMissionTime()", "game-time seconds since mission start, not time since phase entry", effect="current mission clock"),
    _entry("after", "function", [(('Number',), 'Bool')], "lowered", "GameGetMissionTime() >= seconds", "nonnegative absolute mission-time threshold; eventless transition polls every 1s", effect="deadline reached, even when phase starts after deadline"),
    _entry("strength", "function", [(('Force',), 'Float')], "unsupported", "none", "no unit-strength metric in backend"),
    _entry("player_unit_count", "function", [(('Force',), 'Int')], "lowered", "UnitGroupCount(UnitGroup(null, owner, entire map, default filter), alive)", "force binding with numeric owner", effect="owner-wide live units matching default filter, not force roster or observer visibility"),
    _entry("apparent_count", "function", [(('Force',), 'Int')], "lowered", "UnitGroupCount(UnitGroup(null, owner, entire map, default filter), alive)", "compatibility alias; prefer player_unit_count", effect="owner-wide live units matching default filter, not observer-visible count", alias="player_unit_count"),
    _entry("enter", "event", [(('Force','Region'), 'Any')], "lowered", "TriggerAddEventUnitRegion + EventUnit membership", "bound force and circle", effect="matching unit entered region"),
    _entry("leave", "event", [(('Force','Region'), 'Any')], "lowered", "TriggerAddEventUnitRegion + EventUnit membership", "bound force and circle", effect="matching unit left region"),
    _entry("unit_died", "event", [(('Entity',), 'Any'), (('Force',), 'Any'), (('Entity','Force'), 'Any')], "lowered", "TriggerAddEventUnitDied + EventUnit + libNtve_gf_KillingUnit membership", "stable victim roster; optional killer force may be absent for environmental deaths", effect="bound victim death and, when specified, killer membership observed"),
    _entry("unit_attacked", "event", [(('Entity',), 'Any'), (('Entity','Force'), 'Any')], "lowered", "TriggerAddEventUnitAttacked2 + EventUnit + EventUnitTarget membership", "bound victim; optional attacking force uses stable group identity", effect="victim attacked by specified force; neither damage nor sustained targeting implied"),
    _entry("unit_became_idle", "event", [(('Force',), 'Any')], "lowered", "TriggerAddEventUnitBecomesIdle(trigger,null,true) + EventUnit membership", "event denotes one bound member becoming idle, not all group members", effect="one member becomes idle; arrival and phase completion need separate conditions"),
    _entry("ability_completed", "event", [(('Entity','String'), 'Any'), (('Force','String'), 'Any')], "lowered", "TriggerAddEventUnitAbility(c_unitAbilStageComplete)", "ability identifier must match game's data; unit match", effect="ability completion event"),
    _entry("ability_cast", "event", [(('Entity','String'), 'Any'), (('Force','String'), 'Any')], "lowered", "TriggerAddEventUnitAbility(c_abilEffectStageCast)", "ability identifier must match game's data; unit match", effect="cast-stage event"),
    _entry("construction_completed", "event", [(('Asset',), 'Any')], "lowered", "TriggerAddEventUnitConstructProgress(c_unitProgressStageComplete)", "bound asset", effect="construction completion event"),
    _entry("move", "action", [(('Force','Region'), 'Any'), (('Force','Route'), 'Any'), (('Force','Location'), 'Any')], "lowered", "UnitGroupIssueOrder(move, center)", "target needs concrete point; Route is strategic only", "order requested", "arrival needs enter/count_in check", "enemy -> Galaxy; ally -> intent"),
    _entry("attack", "action", [(('Force','Entity'), 'Any'), (('Force','Force'), 'Any'), (('Force','Asset'), 'Any')], "lowered", "UnitGroupIssueOrder(attack, target group)", "bound group target", "order requested", "damage/kill needs observed evidence", "enemy -> Galaxy; ally -> intent"),
    _entry("hold", "action", [(('Force',), 'Any')], "lowered", "UnitGroupIssueOrder(stop)", "bound force", "stop order requested", "no guaranteed sustained hold", "enemy -> Galaxy; ally -> intent"),
    _entry("retreat", "action", [(('Force','Region'), 'Any'), (('Force','Route'), 'Any'), (('Force','Location'), 'Any')], "lowered", "UnitGroupIssueOrder(move, center)", "point target; Route is strategic only", "move order requested", "safe escape needs enter/count_in check", "enemy -> Galaxy; ally -> intent"),
    _entry("retarget", "action", [(('Force','Force'), 'Any'), (('Force','Asset'), 'Any'), (('Force','Entity'), 'Any')], "lowered", "UnitGroupIssueOrder(attack or move)", "same-side target -> move to spawn point; opposing side -> attack", "order requested", "response and weakened defense need separate observation", "enemy -> Galaxy; ally -> intent"),
    _entry("transport", "action", [(('Force','Force','Region'), 'Any'), (('Force','Force','Location'), 'Any')], "unsupported", "none", "no transport lowerer", actor="enemy -> unsupported; ally -> intent"),
    _entry("cast", "action", [(('Force','String'), 'Any'), (('Force','String','Entity'), 'Any'), (('Force','String','Region'), 'Any')], "lowered", "UnitGroupIssueOrder(AbilityCommand(...))", "ability string and target shape require game-data validation", "order requested", "ability effect needs event/state check", "enemy -> Galaxy; ally -> intent"),
    _entry("set_mode", "action", [(('Entity','String'), 'Any')], "lowered", "UnitGroupIssueOrder(AbilityCommand(mode))", "mode must map to a real ability for unit type", "order requested", "mode state needs observation", "enemy -> Galaxy; ally -> intent"),
    _entry("control", "action", [(('Force','Force'), 'Any')], "unsupported", "none", "no control lowerer", actor="enemy -> unsupported; ally -> intent"),
    _entry("build", "action", [(('Force','Asset','Region'), 'Any')], "unsupported", "none", "no build lowerer", actor="enemy -> unsupported; ally -> intent"),
    _entry("cancel", "action", [(('Asset',), 'Any')], "unsupported", "none", "no cancel lowerer", actor="enemy -> unsupported; ally -> intent"),
    _entry("spawn", "action", [(('Force','Region'), 'Any'), (('Force','Location'), 'Any')], "lowered", "CreateUnits + add to stable group", "spawn components and concrete target point", "create requested", "live unit count/position for effect", "enemy -> Galaxy; ally -> intent"),
    _entry("block", "action", [(('Force','Region'), 'Any')], "lowered", "UnitGroupIssueOrder(ForceField, center)", "unit must actually have ForceField ability; region center", "order requested", "path denial needs observed check", "enemy -> Galaxy; ally -> intent"),
]

# Compatibility facilities assumed by Claude's interaction patch.
_ROWS += [
    _entry("elapsed", "function", [(("Any",), "Float")], "lowered", "GameGetMissionTime() - phase entry time", "phase name; entry-relative game seconds"),
    _entry("life_ratio", "function", [(("Entity",), "Float")], "lowered", "sum current life / sum maximum life", "alive members; empty group returns zero"),
    _entry("nearest_distance", "function", [(("Entity", "Entity"), "Float")], "lowered", "minimum live member pair distance", "alive groups; no pairs return sentinel"),
    _entry("has_status", "function", [(("Entity", "String"), "Bool")], "lowered", "any live member has behavior", "game-data behavior link"),
    _entry("visible_to", "function", [(("String", "Entity"), "Bool"), (("String", "Region"), "Bool")], "lowered", "unit visibility or region-center visibility", "single-player side; region query observes center"),
    _entry("count_matching", "function", [(("Entity", "String"), "Int")], "lowered", "UnitFilterMatch over alive bound members", "validated filter names"),
    _entry("event_source_in", "function", [(("Entity",), "Bool")], "special_context", "event-specific source unit membership", "matching event context only"),
    _entry("event_target_in", "function", [(("Entity",), "Bool")], "special_context", "event-specific target unit membership", "matching event context only"),
    _entry("event_in", "function", [(("Region",), "Bool")], "special_context", "event subject within bound region", "unit event only"),
    _entry("event_amount", "function", [((), "Float")], "special_context", "event-specific numeric amount", "matching event context only"),
    _entry("unit_damaged", "event", [(("Entity",), "Any")], "lowered", "TriggerAddEventUnitDamaged + victim membership", "bound victim roster"),
    _entry("effect_used", "event", [(("Entity", "String"), "Any")], "lowered", "TriggerAddEventEffectUsed + caster membership", "game-data effect link"),
    _entry("timer", "event", [(("Any", "Number"), "Any")], "lowered", "phase-local one-shot timer", "phase name and positive duration; starts at entry"),
    # v0.6 Petri-net marking observers (the plan's own state, not the world).
    _entry("tokens", "function", [(("Any",), "Int")], "lowered", "marking global gv_net_m_<place>", "plan place or phase name; reads the token count of the plan net", effect="exact current marking"),
    _entry("active", "function", [(("Any",), "Bool")], "lowered", "gv_net_m_<place> > 0", "plan place or phase name; true while it holds a token", effect="exact current marking"),
    _entry("apply_effect", "action", [(("Entity", "String", "Entity"), "Any")], "lowered", "UnitCreateEffectUnit", "script effect; game-data link validation remains external", actor="environment"),
]
# These old names now have an observable lowering / point-target overload.
from dataclasses import replace as _replace
for _i, _r in enumerate(_ROWS):
    if _r.name == "targeting" and _r.namespace == "function":
        _ROWS[_i] = _replace(_r, signatures=(Signature(("Force", "Entity"), "Bool"), Signature(("Force", "Region"), "Bool")), backend="lowered", galaxy="current live unit order target", prerequisites="observable order target; does not establish damage", effect_evidence="current command target only")
    elif _r.name in {"control", "build"} and _r.namespace == "action":
        _ROWS[_i] = _replace(_r, backend="lowered", galaxy="v04 scripted ownership rewrite" if _r.name == "control" else "v04 scripted construction spawn", prerequisites="environment operation; not simulated worker control", actor="enemy -> Galaxy; ally -> intent")
    elif _r.name == "retarget" and _r.namespace == "action":
        _ROWS[_i] = _replace(_r, signatures=_r.signatures + (Signature(("Force", "Region"), "Any"),))

REGISTRY: dict[tuple[str, str], ApiSpec] = {(r.namespace, r.name): r for r in _ROWS}
assert len(REGISTRY) == len(_ROWS), "duplicate API contract"


def contracts(namespace: str | None = None) -> tuple[ApiSpec, ...]:
    return tuple(sorted((r for r in REGISTRY.values() if namespace is None or namespace == r.namespace), key=lambda r: (r.namespace, r.name)))


def signature_table(namespace: str) -> dict[str, list[Signature]]:
    return {r.name: list(r.signatures) for r in contracts(namespace)}


def catalog_json() -> dict:
    return {"format": "stratagemdsl.api-contracts.v1", "apis": [asdict(r) for r in contracts()]}


def catalog_markdown() -> str:
    lines = ["# StratagemDSL API contracts", "", "Signatures come from the same registry as the type checker and LLM tool schema. `lowered` describes an existing compiler mapping, not a proven runtime outcome. Agent-side actions remain strategic intent.", ""]
    for ns, title in (("function", "Predicates and metrics"), ("event", "Transition events"), ("action", "Plan actions")):
        lines += [f"## {title}", "", "| API / signature | Backend | Galaxy mapping | Preconditions | Order evidence | Effect evidence | Actor |", "| --- | --- | --- | --- | --- | --- | --- |"]
        for r in contracts(ns):
            names = ", ".join(f"`{r.name}({', '.join(s.args)}) -> {s.returns}`" for s in r.signatures)
            if r.alias_of: names += f" (alias: `{r.alias_of}`)"
            cells = (names, r.backend, r.galaxy, r.prerequisites, r.issue_evidence, r.effect_evidence, r.actor)
            lines.append("| " + " | ".join(x.replace("|", "\\|").replace("\n", " ") for x in cells) + " |")
        lines.append("")
    lines += ["## Deliberately absent APIs", "", "- `visible_count(observer, force)`: no observer-specific visibility semantics until fog, ownership, and visibility queries are modeled together.", "- `can_reach(force, region)` is now implemented: at least one live member can reach the region center; this does not prove the whole group can traverse the entire region.", "- `group_idle(force)` and `phase until idle(...)`: a per-unit idle event does not establish group completion, arrival, or success.", "- `role`: a free-text strategic hint used for pattern diagnostics; it has no implicit Galaxy lowering.", ""]
    return "\n".join(lines)


def register_interaction_contracts(functions, events, actions):
    """Mirror executable extension signatures into the canonical exported catalog."""
    for namespace, table in (("function", functions), ("event", events), ("action", actions)):
        for name, entry in table.items():
            sigs, scope = entry if namespace == "action" else (entry, "none")
            signatures = tuple(sigs)
            old = REGISTRY.get((namespace, name))
            REGISTRY[(namespace, name)] = ApiSpec(
                name, namespace, signatures,
                "special_context" if name.startswith("event_") else "lowered",
                "v04 registry mapping: " + name,
                "game-data links require engine validation",
                "order requested" if scope == "order" else "",
                "compiler mapping only; outcome requires observation",
                "enemy -> Galaxy; ally -> intent" if scope == "order" else "environment" if namespace == "action" else "none",
                old.alias_of if old else "",
            )
