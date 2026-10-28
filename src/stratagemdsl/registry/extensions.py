"""Interaction API registry: signatures, literal vocabularies and scopes.

Layer 2 (registry). This module only *declares* the language surface added in
v0.4/v0.5: each call's type signatures, which string literals an argument may
take, which events an event-context function may be used in, and the scope of
each action (order / env / rewrite). The Galaxy text for every entry lives in
``stratagemdsl.backend.galaxy.extensions``; the validator never imports it.

Vocabulary tables map a DSL literal to the engine constant the backend emits;
the checker only uses their keys.
"""
from __future__ import annotations

from typing import Any

from stratagemdsl.registry.builtins import (
    ACTIONS, EVENT_CONTEXT, EVENTS, FUNCTIONS, PHASE_ARGS, TARGET_FILTER_BITS, Signature,
)
from stratagemdsl.registry.contracts import register_interaction_contracts
def S(*args: str, ret: str = "Any") -> Signature:
    return Signature(tuple(args), ret)


# ------------------------------------------------------------------ vocabularies
SIDES = {"ally": 1, "enemy": 2}
PLAYER_PROPS = {"minerals": "c_playerPropMinerals", "vespene": "c_playerPropVespene",
                "supply_used": "c_playerPropSuppliesUsed", "supply_limit": "c_playerPropSuppliesLimit"}
SUPPLY = {"used": "c_playerPropSuppliesUsed", "limit": "c_playerPropSuppliesLimit", "made": "c_playerPropSuppliesMade"}
ABIL_STAGES = {"approach": "c_abilEffectStageApproach", "prep": "c_abilEffectStagePrep", "cast": "c_abilEffectStageCast",
               "channel": "c_abilEffectStageChannel", "finish": "c_abilEffectStageFinish", "bail": "c_abilEffectStageBail",
               "cancel": "c_unitAbilStageCancel", "preempt": "c_unitAbilStagePreempt", "complete": "c_unitAbilStageComplete",
               "execute": "c_unitAbilStageExecute", "queue": "c_unitAbilStageQueue"}
AUTOCAST = {"on": "c_unitAbilAutoCastChangeOn", "off": "c_unitAbilAutoCastChangeOff"}
BEHAVIOR_CATEGORIES = {n: f"c_behaviorCategory{n}" for n in (
    "Aura", "CanSteal", "Cloak", "Fast", "Invulnerable", "Magic", "Passive", "PassiveMagic", "Permanent",
    "Physical", "Restorable", "Reveal", "Slow", "Stun", "TeleportRemove", "Temporary", "TimedLife")}
VITAL_PROPS = {"life": "c_unitPropLife", "shields": "c_unitPropShields", "energy": "c_unitPropEnergy"}
VITALS = {"life": "c_unitVitalLife", "shields": "c_unitVitalShields", "energy": "c_unitVitalEnergy"}
DAMAGE_KINDS = {"attempted": "EventUnitDamageAttempted()", "absorbed": "EventUnitDamageAbsorbed()",
                "shield_absorbed": "EventUnitDamageBehaviorShield()", "vital_attempted": "EventUnitDamageAttemptedVitals()"}
DEATH_TYPES = {"normal": "c_deathTypeNormal", "timeout": "c_deathTypeTimeout", "remove": "c_deathTypeRemove",
               "cancel": "c_deathTypeCancel", "morph": "c_deathTypeMorph", "blast": "c_deathTypeBlast",
               "disintegrate": "c_deathTypeDisintegrate", "eat": "c_deathTypeEat", "fire": "c_deathTypeFire",
               "freeze": "c_deathTypeFreeze", "impact": "c_deathTypeImpact", "silentkill": "c_deathTypeSilentkill",
               "squish": "c_deathTypeSquish", "salvage": "c_deathTypeSalvage", "unlink": "c_deathTypeUnlink",
               "under_construction": "c_deathTypeUnderConstruction"}
PATHING = {"unpathable": "c_pathingUnpathable", "ground": "c_pathingGround", "building": "c_pathingBuilding", "cliff": "c_pathingCliff"}
UNIT_STATES = {"cloaked": "c_unitStateCloaked", "buried": "c_unitStateBuried", "stunned": "c_unitStateStunned",
               "hallucination": "c_unitStateHallucination", "detector": "c_unitStateDetector", "in_stasis": "c_unitStateInStasis",
               "silenced": "c_unitStateSilenced", "idle": "c_unitStateIdle", "invulnerable": "c_unitStateInvulnerable",
               "hidden": "c_unitStateHidden", "paused": "c_unitStatePaused", "radar": "c_unitStateRadar",
               "attack_suppressed": "c_unitStateAttackSuppressed", "move_suppressed": "c_unitStateMoveSuppressed",
               "dazed": "c_unitStateDazed", "inside_transport": "c_unitStateInsideTransport", "is_transport": "c_unitStateIsTransport",
               "changeling": "c_unitStateIsChangeling", "sleeping": "c_unitStateSleeping", "resistant": "c_unitStateResistant",
               "targetable": "c_unitStateTargetable", "selectable": "c_unitStateSelectable", "detectable": "c_unitStateDetectable"}
TECH_KINDS = {"unit", "upgrade", "behavior", "ability"}
FILL_TYPES = {"fogged": "c_fillTypeFogged", "masked": "c_fillTypeMasked", "hidden": "c_fillTypeHidden", "unexplored": "c_fillTypeUnexplored"}
ALLIANCE = {"ally": "libNtve_ge_AllianceSetting_Ally", "ally_vision": "libNtve_ge_AllianceSetting_AllyWithSharedVision",
            "ally_vision_control": "libNtve_ge_AllianceSetting_AllyWithSharedVisionAndControl",
            "enemy": "libNtve_ge_AllianceSetting_Enemy", "enemy_vision": "libNtve_ge_AllianceSetting_EnemyWithSharedVision",
            "neutral": "libNtve_ge_AllianceSetting_Neutral", "neutral_vision": "libNtve_ge_AllianceSetting_NeutralWithSharedVision"}
DAMAGE_DIR = {"deal": "libNtve_ge_UnitDamageTakenDealt_Damage_Deal", "take": "libNtve_ge_UnitDamageTakenDealt_Damage_Take"}
DAMAGE_OPT = {"full": "libNtve_ge_UnitDamageChangeOption_Full", "no": "libNtve_ge_UnitDamageChangeOption_No",
              "minimal": "libNtve_ge_UnitDamageChangeOption_Minimal", "mega": "libNtve_ge_UnitDamageChangeOption_Mega",
              "mega2": "libNtve_ge_UnitDamageChangeOption_Mega2"}
REGEN = {"full", "remaining"}
REACT_ROLES = {"subject", "source"}
FILTER_ALLIANCE_BITS = {"Self": 0, "Player": 1, "Ally": 2, "Neutral": 3, "Enemy": 4, "NeutralHostile": 61}

# (call name, arg index) -> vocabulary (dict/set) or "side". Checked by the validator (T101 / T091).
VOCAB: dict[tuple[str, int], Any] = {}

# memory functions: name -> (kind, mode) ; mode w=write r=read a=any
MEMORY: dict[str, tuple[str, str]] = {
    "remember": ("number", "w"), "recall": ("number", "r"),
    "tally": ("count", "w"), "tallied": ("count", "r"),
    "mark": ("flag", "w"), "unmark": ("flag", "w"), "marked": ("flag", "r"),
    "snapshot": ("snapshot", "w"), "count_snapshot": ("snapshot", "r"), "snapshot_lost": ("snapshot", "r"),
    "remember_event_unit": ("unit", "w"), "remembered_alive": ("unit", "r"), "remembered_in": ("unit", "r"),
    "remember_position": ("position", "w"), "near_remembered": ("position", "r"),
    "choose": ("choice", "w"), "chosen": ("choice", "r"),
    "forget": ("*", "a"), "known": ("*", "a"),
}
MEMORY_KEY_INDEX = {"remembered_in": 1, "near_remembered": 1}  # default 0
CTX: dict[str, frozenset] = {}   # event-context function -> events it may be used in
REWRITE_ACTIONS: set[str] = set()

# ------------------------------------------------------------------ registries
FUNCS: dict[str, list[Signature]] = {}                  # name -> signatures
EVS: dict[str, list[Signature]] = {}                    # name -> signatures
ACTS: dict[str, tuple[list[Signature], str]] = {}       # name -> (signatures, scope)


def _record_vocab(name, vocab):
    for i, v in (vocab or {}).items():
        VOCAB[(name, i)] = v


def fn(name, *sigs, vocab=None, ctx=None):
    """Declare a function; ``ctx`` lists the events it may be evaluated in."""
    FUNCS[name] = list(sigs)
    _record_vocab(name, vocab)
    if ctx:
        CTX[name] = frozenset(ctx)


def ev(name, *sigs, vocab=None):
    EVS[name] = list(sigs)
    _record_vocab(name, vocab)


def act(name, *sigs, scope="env", vocab=None):
    """scope: order (enemy actor is emitted, ally actor becomes an agent intent),
    env (script/environment, always emitted), rewrite (always emitted, W110)."""
    ACTS[name] = (list(sigs), scope)
    _record_vocab(name, vocab)
    if scope == "rewrite":
        REWRITE_ACTIONS.add(name)

ev("property_changed", S("String", "String"), vocab={0: "side", 1: PLAYER_PROPS})
ev("upgrade_changed", S("String", "String"), vocab={0: "side"})
ev("side_left", S("String"), vocab={0: "side"})
ev("ability_stage", S("Entity", "String", "String"), vocab={2: ABIL_STAGES})
ev("autocast_changed", S("Entity", "String", "String"), vocab={2: AUTOCAST})
ev("status_class_gained", S("Entity", "String"), vocab={1: BEHAVIOR_CATEGORIES})
ev("status_class_lost", S("Entity", "String"), vocab={1: BEHAVIOR_CATEGORIES})
ev("damage_absorbed", S("Entity", "String"))
ev("research_done", S("Entity", "String"))
ev("trained", S("Entity", "String"))
ev("vital_changed", S("Entity", "String"), vocab={1: VITAL_PROPS})
ev("produced", S("Entity", "String"))
ev("unit_healed", S("Entity"))
ev("loaded", S("Entity"))
ev("unloaded", S("Entity"))
ev("acquired_target", S("Entity"))
ev("attack_started", S("Entity"))


# ------------------------------------------------------------------ event-context functions
PLAYER_EVENTS = {"property_changed", "upgrade_changed", "side_left"}
UNIT_EVENTS = {"enter", "leave", "unit_died", "unit_attacked", "unit_damaged", "ability_cast", "ability_completed",
               "construction_completed", "effect_used", "ability_stage", "autocast_changed", "status_class_gained",
               "status_class_lost", "damage_absorbed", "research_done", "trained", "vital_changed", "produced",
               "unit_healed", "loaded", "unloaded", "acquired_target", "attack_started"}
ABILITY_EVENTS = {"ability_cast", "ability_completed", "ability_stage"}
# Events that carry a numeric amount (event_amount) / a source player (event_source_side).
AMOUNT_EVENTS = frozenset({"property_changed", "upgrade_changed", "vital_changed", "unit_healed", "damage_absorbed"})
SIDE_SOURCE_EVENTS = {"unit_healed", "unit_damaged", "unit_died"}
fn("event_ability_is", S("String", ret="Bool"), ctx=ABILITY_EVENTS)
fn("event_stage_is", S("String", ret="Bool"), ctx=ABILITY_EVENTS, vocab={0: ABIL_STAGES})
fn("event_other_in", S("Entity", ret="Bool"), ctx=ABILITY_EVENTS)
fn("event_cargo_in", S("Entity", ret="Bool"), ctx={"loaded", "unloaded"})
fn("event_damage", S("String", ret="Float"), ctx={"unit_damaged", "damage_absorbed"}, vocab={0: DAMAGE_KINDS})
fn("event_leeched", S("String", ret="Float"), ctx={"unit_damaged"}, vocab={0: VITALS})
fn("event_source_at", S("Region", ret="Bool"), ctx={"unit_damaged"})
fn("event_weapon_is", S("String", ret="Bool"), ctx={"unit_attacked", "attack_started"})
fn("event_death_is", S("String", ret="Bool"), ctx={"unit_died"}, vocab={0: DEATH_TYPES})
fn("event_effect_is", S("String", ret="Bool"), ctx={"unit_healed", "unit_damaged"})
fn("event_source_side", S("String", ret="Bool"), ctx=SIDE_SOURCE_EVENTS, vocab={0: "side"})
fn("event_vital_is", S("String", ret="Bool"), ctx={"unit_healed"}, vocab={0: VITALS})
fn("event_object_is", S("String", ret="Bool"), ctx={"construction_completed", "trained", "research_done"})
fn("event_product_in", S("Entity", ret="Bool"), ctx={"construction_completed", "trained"})
fn("event_created_by", S("String", ret="Bool"), ctx={"produced"})
fn("event_created_by_status", S("String", ret="Bool"), ctx={"produced"})
# ------------------------------------------------------------------ memory / time
fn("recall", S("String", ret="Float"))
fn("tallied", S("String", ret="Int"))
fn("known", S("String", ret="Bool"))
fn("marked", S("String", ret="Bool"))
fn("count_snapshot", S("String", ret="Int"))
fn("snapshot_lost", S("String", ret="Int"))
fn("remembered_alive", S("String", ret="Bool"))
fn("remembered_in", S("Entity", "String", ret="Bool"))
fn("near_remembered", S("Entity", "String", "Number", ret="Bool"))
fn("chosen", S("String", "String", ret="Bool"))
fn("count_tagged", S("Entity", "String", "Number", ret="Int"))
fn("window_held", S("Phase", "Number", ret="Bool"))
fn("hostile", S("String", "String", ret="Bool"), vocab={0: "side", 1: "side"})
fn("hostile_mutual", S("String", "String", ret="Bool"), vocab={0: "side", 1: "side"})
fn("allied", S("String", "String", ret="Bool"), vocab={0: "side", 1: "side"})
fn("side_size", S("String", ret="Int"), vocab={0: "side"})
fn("bearing", S("Entity", "Entity", ret="Float"), S("Entity", "Region", ret="Float"))
fn("flank_angle", S("Entity", "Entity", "Entity", ret="Float"))
fn("pathing_is", S("Region", "String", ret="Bool"), vocab={1: PATHING})
fn("can_reach", S("Force", "Entity", ret="Bool"), S("Force", "Region", ret="Bool"))


def filter_masks(spec: str) -> tuple[list[str], list[str], list[str]]:
    req, exc, errors = [], [], []
    names = {**TARGET_FILTER_BITS, **FILTER_ALLIANCE_BITS}
    for raw_t in spec.split(","):
        t = raw_t.strip()
        neg = t.startswith("-")
        n = t[1:].strip() if neg else t
        if n not in names:
            errors.append(f"unknown target filter '{n}'")
        elif n in req or n in exc:
            errors.append(f"filter '{n}' listed twice")
        else:
            (exc if neg else req).append(n)
    return req, exc, errors
fn("count_matching_vs", S("Entity", "String", "String", ret="Int"), vocab={1: "side"})
fn("can_attack", S("Force", "Entity", ret="Bool"))
fn("count_owned", S("Entity", "String", ret="Int"), vocab={1: "side"})
# ------------------------------------------------------------------ perception
fn("creep_adjacent", S("Region", ret="Int"))
fn("powered", S("Entity", ret="Bool"))
fn("powered_by", S("Entity", "Entity", ret="Bool"))
# ------------------------------------------------------------------ queries
fn("supply", S("String", "String", ret="Float"), vocab={0: "side", 1: SUPPLY})
fn("race_is", S("String", "String", ret="Bool"), vocab={0: "side"})
fn("score", S("String", "String", ret="Float"), vocab={0: "side"})
fn("score_count", S("String", "String", ret="Int"), vocab={0: "side"})
fn("side_active", S("String", ret="Bool"), vocab={0: "side"})
fn("status_count", S("String", "String", ret="Int"), vocab={0: "side"})
fn("ability_count", S("String", "String", ret="Int"), vocab={0: "side"})
for _name, _sig in [
    ("queued", S("Entity", "String", ret="Int")),
    ("unit_status_count", S("Entity", "String", ret="Int")),
    ("unit_upgrade_count", S("Entity", "String", ret="Int")),
    ("has_ability", S("Entity", "String", ret="Bool")),
    ("ability_enabled", S("Entity", "String", ret="Bool")),
    ("ability_level", S("Entity", "String", ret="Float")),
    ("summoned_with", S("Entity", "String", ret="Bool")),
    ("shield_left", S("Entity", "String", ret="Float")),
    ("status_fraction_left", S("Entity", "String", ret="Float")),
    ("status_active", S("Entity", "String", ret="Bool")),
    ("carried", S("Entity", ret="Bool")),
    ("cooldown_left", S("Entity", "String", ret="Float")),
    ("charges_used", S("Entity", "String", ret="Float")),
    ("charge_regen_left", S("Entity", "String", ret="Float")),
    ("ability_charges_used", S("Entity", "String", "String", ret="Float")),
    ("ability_charge_regen_left", S("Entity", "String", "String", ret="Float")),
    ("status_cooldown_left", S("Entity", "String", "String", ret="Float")),
    ("status_charges_used", S("Entity", "String", "String", ret="Float")),
    ("status_charge_regen_left", S("Entity", "String", "String", ret="Float")),
    ("producing", S("Entity", ret="Bool")),
    ("train_progress", S("Entity", ret="Float")),
    ("queue_used", S("Entity", ret="Int")),
    ("under_construction", S("Entity", ret="Bool")),
    ("has_addon", S("Entity", ret="Bool")),
    ("airborne", S("Entity", ret="Bool")),
    ("army_value", S("Entity", ret="Int")),
    ("resources_left", S("Entity", ret="Int")),
    ("invulnerable", S("Entity", ret="Bool")),
    ("firepower", S("Force", ret="Float")),
    ("engaging", S("Entity", ret="Bool")),
    ("ordered_with", S("Entity", "String", ret="Bool")),
    ("damaged_with", S("Entity", "String", ret="Bool")),
]:
    fn(_name, _sig)
fn("tech_allowed", S("String", "String", "String", ret="Bool"), vocab={0: "side", 1: TECH_KINDS})
fn("summoned_by", S("Entity", "Entity", ret="Bool"))
fn("cargo_count", S("Entity", ret="Int"))
fn("cargo_space", S("Entity", ret="Int"))
fn("carried_by", S("Entity", "Entity", ret="Bool"))
fn("state", S("Entity", "String", ret="Bool"), vocab={1: UNIT_STATES})
fn("combat_power", S("Force", ret="Float"))
fn("rallied_to", S("Entity", "Region", ret="Bool"))
fn("damaged_by", S("Entity", "Entity", "Number", ret="Bool"))
fn("damage_from", S("Entity", "Entity", ret="Int"))
fn("status_source_in", S("Entity", "String", "Entity", ret="Bool"))
fn("status_source_side", S("Entity", "String", "String", ret="Bool"), vocab={2: "side"})
fn("order_rejected", S("Force", ret="Bool"))
fn("idle_count", S("Entity", ret="Int"))
# ------------------------------------------------------------------ actions: memory / time / env
act("remember", S("String", "Number"))
act("tally", S("String", "Number"))
act("forget", S("String"))
act("mark", S("String"))
act("unmark", S("String"))
act("snapshot", S("String", "Entity"))
act("remember_event_unit", S("String", "String"), vocab={1: REACT_ROLES})
act("remember_position", S("String", "Entity"))
act("choose", S("String", "String"))
act("tag", S("Entity", "String", "Number"))
act("hold_window", S("Phase", "Number"))
act("resume_window", S("Phase", "Number"))
act("restart_window", S("Phase", "Number"))
act("no_fly", S("Region"))
act("clear_no_fly", S("Region"))
act("reveal", S("String", "Region", "Number"), vocab={0: "side"})
act("reveal_while", S("String", "Region"), vocab={0: "side"})
act("recenter", S("Region", "Entity"))
act("transfer", S("Force", "Force"))
act("detach", S("Force", "Number", "Force"))
act("release", S("Force", "Entity"))


T_ARG = {"side": "String", "point": None, "str": "String", "num": "Number", "int": "Number", "bool": "Bool",
         "cat": "String", "state": "String", "vital_prop": "String", "unit1": "Entity"}
for _name, _fmt, _vocab in [
    ("force_kill", (), {}),
    ("force_remove", (), {}),
    ("force_owner", ("side",), {1: "side"}),
    ("rescue", ("side",), {1: "side"}),
    ("force_teleport", ("point",), {}),
    ("force_face", ("point",), {}),
    ("force_pause", ("bool",), {}),
    ("force_hide", ("bool",), {}),
    ("force_sleep", ("bool",), {}),
    ("force_replace", ("str",), {}),
    ("force_disable", ("str",), {}),
    ("force_status", ("str", "side", "int"), {2: "side"}),
    ("force_status_off", ("str", "side", "int"), {2: "side"}),
    ("strip_status", ("cat",), {1: BEHAVIOR_CATEGORIES}),
    ("force_status_remaining", ("str", "num"), {}),
    ("force_status_duration", ("str", "num"), {}),
    ("force_status_stacks", ("str", "int"), {}),
    ("transfer_status", ("unit1", "str"), {}),
    ("reset_cooldowns", (), {}),
    ("force_cooldown", ("str", "num"), {}),
    ("clear_cooldown", ("str",), {}),
    ("spend_charges", ("str", "num"), {}),
    ("restore_charges", ("str",), {}),
    ("force_ability_cooldown", ("str", "str", "num"), {}),
    ("clear_ability_cooldown", ("str", "str"), {}),
    ("spend_ability_charges", ("str", "str", "num"), {}),
    ("restore_ability_charges", ("str", "str"), {}),
    ("reset_ability", ("str",), {}),
    ("force_status_cooldown", ("str", "str", "num"), {}),
    ("clear_status_cooldown", ("str", "str"), {}),
    ("spend_status_charges", ("str", "str", "num"), {}),
    ("restore_status_charges", ("str", "str"), {}),
    ("force_vital", ("vital_prop", "num"), {1: VITAL_PROPS}),
    ("pause_progress", (), {}),
    ("force_state", ("state", "bool"), {1: UNIT_STATES}),
]:
    _sig = S("Entity", *[T_ARG[k] or "Location" for k in _fmt])
    if "point" in _fmt:
        _sig = S("Entity", *[("Region" if k == "point" else T_ARG[k]) for k in _fmt])
    act(_name, _sig, scope="rewrite", vocab=_vocab)
act("force_enable", S("Entity", "String"), scope="rewrite")
act("force_charge_regen", S("Entity", "String", "Number", "String"), scope="rewrite", vocab={3: REGEN})
act("force_ability_charge_regen", S("Entity", "String", "String", "Number", "String"), scope="rewrite", vocab={4: REGEN})
act("force_status_charge_regen", S("Entity", "String", "String", "Number", "String"), scope="rewrite", vocab={4: REGEN})
act("force_alliance", S("String", "String", "String"), scope="rewrite", vocab={0: "side", 1: "side", 2: ALLIANCE})
act("force_upgrade", S("String", "String", "Number"), scope="rewrite", vocab={0: "side"})
# ------------------------------------------------------------------ publish into the shared tables
for _n, _sigs in FUNCS.items():
    if _n not in FUNCTIONS:
        FUNCTIONS[_n] = _sigs
for _n, _sigs in EVS.items():
    EVENTS[_n] = _sigs
for _n, (_sigs, _scope) in ACTS.items():
    ACTIONS[_n] = _sigs
for _n, _evs in CTX.items():
    EVENT_CONTEXT[_n] = _evs
EVENT_CONTEXT["event_amount"] = EVENT_CONTEXT["event_amount"] | AMOUNT_EVENTS
EVENT_CONTEXT["event_source_in"] = EVENT_CONTEXT["event_source_in"] | frozenset({"unit_healed"})
EVENT_CONTEXT["event_target_in"] = EVENT_CONTEXT["event_target_in"] | frozenset({"acquired_target"})
EVENT_CONTEXT["event_in"] = frozenset(UNIT_EVENTS)
for _n in ("window_held", "hold_window", "resume_window", "restart_window"):
    PHASE_ARGS[_n] = (0,)

# Keep the exported API catalogue and LLM schema in sync with the extensions.
register_interaction_contracts(FUNCS, EVS, ACTS)

ORDER_ACTIONS = {"attack", "retarget", "move", "retreat", "hold", "set_mode", "cast", "block"}
# Script-level actions: always emitted regardless of the actor's side.
ALWAYS_EMIT = {n for n, (_s, scope) in ACTS.items() if scope in ("env", "rewrite")}
SETUP_REWRITE_KEYS = {"alliance", "tech", "ability", "share_vision", "cargo", "progress", "damage", "invulnerable",
                      "uncommandable", "weapons", "playable", "asleep"}


V03_SETUP_ITEMS = {"minerals", "supplies_made", "upgrade", "creep", "remove_behavior", "tech_requirements"}
