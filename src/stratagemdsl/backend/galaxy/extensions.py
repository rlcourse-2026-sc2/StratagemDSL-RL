"""Galaxy lowering for the interaction APIs declared in registry.extensions.

Layer 4 (backend). Every entry registered here is the Galaxy text for one name
in ``registry.extensions``; ``tests/l4_backend`` checks that both tables cover
the same names. Design rules:

* no grammar change -- everything is a call, an event, an action or a
  setup/binding argument;
* enum constants are emitted as numeric literals (the GUI XML converter
  rejects many named constants outside their parameter presets);
* helpers iterate alive members with index loops and never Wait;
* nothing is emitted unless a strategy uses it, so older sources lower to
  byte-identical Galaxy.
"""
from __future__ import annotations

import re
from typing import Callable, Optional

from stratagemdsl.core.ast_utils import binding_arg as _a, binding_named as _named, walk_calls
from stratagemdsl.core.model import BindingCall, BoolExpr, NameExpr, NumberExpr, StringExpr, UnaryExpr
from stratagemdsl.registry.builtins import TARGET_FILTER_BITS
from stratagemdsl.registry.extensions import (
    ABIL_STAGES, ALLIANCE, AUTOCAST, BEHAVIOR_CATEGORIES, DAMAGE_DIR, DAMAGE_KINDS, DAMAGE_OPT, DEATH_TYPES,
    FILL_TYPES, FILTER_ALLIANCE_BITS, MEMORY, filter_masks, MEMORY_KEY_INDEX, PATHING, PLAYER_PROPS, REACT_ROLES, REGEN,
    SIDES, SUPPLY, TECH_KINDS, UNIT_STATES, V03_SETUP_ITEMS, VITAL_PROPS, VITALS,
)
from stratagemdsl.backend.galaxy.constants import CONSTS
from stratagemdsl.backend.galaxy.errors import LoweringError
from stratagemdsl.backend.galaxy.helper_lib import agg, foreach, pairwise_any, raw

# ------------------------------------------------------------------ lowering tables
LOWER_FN: dict[str, Callable] = {}    # name -> lower(lo, call) -> Galaxy expression
LOWER_EV: dict[str, Callable] = {}    # name -> register(lo, event, trigger) -> (lines, guards)
LOWER_ACT: dict[str, Callable] = {}   # name -> lower(lo, call, indent) -> lines


def _table_decorator(table):
    def register(name):
        def deco(f):
            table[name] = f
            return f
        return deco
    return register


lower_fn = _table_decorator(LOWER_FN)
lower_ev = _table_decorator(LOWER_EV)
lower_act = _table_decorator(LOWER_ACT)

def err(msg: str):
    raise LoweringError(msg)


def K(name: str) -> str:
    """Materialize an enum constant as a numeric literal."""
    v = CONSTS[name]
    return ("true" if v else "false") if isinstance(v, bool) else str(v)


_CONST_RX = re.compile(r"\b(c_[A-Za-z0-9_]+|libNtve_ge_[A-Za-z0-9_]+)\b")


def materialize(text: str) -> str:
    return _CONST_RX.sub(lambda m: K(m.group(1)) if m.group(1) in CONSTS else m.group(1), text)


# ------------------------------------------------------------------ arg helpers
def _arg(e, i):
    if i >= len(e.args):
        err(f"{e.name}(...) misses argument {i + 1}")
    return e.args[i]


def nm(e, i) -> str:
    a = _arg(e, i)
    if not isinstance(a, NameExpr):
        err(f"{e.name}(...) argument {i + 1} must be a name")
    return a.name


def st(e, i) -> str:
    a = _arg(e, i)
    if not isinstance(a, StringExpr):
        err(f"{e.name}(...) argument {i + 1} must be a string literal")
    return a.value


def numv(e, i) -> float:
    a = _arg(e, i)
    if isinstance(a, UnaryExpr) and a.op == "-" and isinstance(a.operand, NumberExpr):
        return -float(a.operand.value)
    if not isinstance(a, NumberExpr):
        err(f"{e.name}(...) argument {i + 1} must be a number literal")
    return float(a.value)


def boo(e, i) -> bool:
    a = _arg(e, i)
    if not isinstance(a, BoolExpr):
        err(f"{e.name}(...) argument {i + 1} must be true/false")
    return a.value


def fx(v: float) -> str:
    return repr(float(v))


def ix(v: float) -> str:
    if not float(v).is_integer():
        err(f"expected a whole number, got {v}")
    return str(int(v))


def gs(s: str) -> str:
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


def voc(e, i, table) -> str:
    v = st(e, i)
    if v not in table:
        err(f"{e.name}(...) argument {i + 1} must be one of {sorted(table)}")
    return v


def side(lo, e, i) -> str:
    return str(lo.ext_player(voc(e, i, SIDES)))


def key(lo, e, i=0) -> str:
    """A strategy-owned user key, disjoint from compiler metadata keys."""
    return gs(lo.ext_state.memory_key(st(e, i)))


def snapshot_size_key(lo, e, i=0) -> str:
    return gs(lo.ext_state.memory_key(st(e, i), kind="snapshot_size"))


def center(lo, name) -> str:
    if lo._world_type(name) == "region":
        return lo._region_geom(name)[0]
    return f"UnitGroupCenterOfGroup({lo._group(name)})"


def need(lo, *helpers):
    for hname in helpers:
        lo._helpers_used.add(hname)


def numexpr(lo, e) -> str:
    """Lower a numeric expression as a Galaxy fixed."""
    if isinstance(e, NumberExpr):
        return fx(e.value)
    text = lo.emit_expr(e)
    return f"IntToFixed({text})" if lo.ext_static_type(e) == "Int" else text


# ------------------------------------------------------------------ helpers (Galaxy)
H: dict[str, list[str]] = {}


def h(spec):
    name, lines = spec
    assert name not in H, name
    H[name] = [materialize(x) for x in lines]


h(agg("gf_S4AnyState", [("int", "lp_state")], "any", "UnitTestState(lv_u, lp_state)"))
h(agg("gf_S4AnyAir", [], "any", "UnitTestPlane(lv_u, c_planeAir)"))
h(pairwise_any("gf_S4CanAttack", [], "libNtve_gf_UnitCanAttackUnit(lv_u, lv_t)"))
h(pairwise_any("gf_S4CanReach", [], "UnitPathableToUnit(lv_u, lv_t, 0.0, 0.0)"))
h(agg("gf_S4CanReachPoint", [("point", "lp_p")], "any", "UnitPathableToPoint(lv_u, lp_p, 0.0, 0.0)"))
h(agg("gf_S4CountMatchVs", [("int", "lp_p"), ("unitfilter", "lp_f")], "count", "UnitFilterMatch(lv_u, lp_p, lp_f)"))
h(agg("gf_S4AllPowered", [], "all", 'PowerLevel(UnitGetOwner(lv_u), UnitGetPosition(lv_u), "PowerSource") > 0'))
h(pairwise_any("gf_S4PoweredBy", [], 'PowerIsProvidedBy(UnitGetOwner(lv_u), UnitGetPosition(lv_u), "PowerSource", lv_t, 1)'))
h(agg("gf_S4HasAbil", [("string", "lp_a")], "any", "UnitAbilityExists(lv_u, lp_a)"))
h(agg("gf_S4AbilEnabled", [("string", "lp_a")], "any", "UnitAbilityCheck(lv_u, lp_a, true)"))
h(agg("gf_S4AbilLevel", [("string", "lp_a")], "max", "IntToFixed(UnitAbilityGetLevel(lv_u, lp_a))"))
h(agg("gf_S4SummonedBy", [("unitgroup", "lp_h")], "any", "UnitGroupHasUnit(lp_h, UnitGetOriginalCaster(lv_u))"))
h(agg("gf_S4SummonedWith", [("string", "lp_e")], "any", "UnitGetOriginalEffect(lv_u) == lp_e"))
h(agg("gf_S4ShieldLeft", [("string", "lp_b")], "sum", "UnitBehaviorDamageModifyRemaining(lv_u, lp_b)"))
h(agg("gf_S4StatusFractionLeft", [("string", "lp_b")], "max",
      "UnitBehaviorDuration(lv_u, lp_b) / MaxF(UnitBehaviorDurationTotal(lv_u, lp_b), 0.0625)"))
h(agg("gf_S4StatusActive", [("string", "lp_b")], "any", "UnitBehaviorEnabled(lv_u, lp_b)"))
h(agg("gf_S4CargoValue", [("int", "lp_prop")], "sum", "UnitCargoValue(lv_u, lp_prop)", rtype="int"))
h(agg("gf_S4Carried", [], "any",
      "libNtve_gf_UnitIsInsideUnitTransport(lv_u) || libNtve_gf_UnitIsInsidePlayerTransport(lv_u)",
      guard="(UnitIsValid(lv_u) == true)"))
h(agg("gf_S4CarriedBy", [("unitgroup", "lp_h")], "any", "UnitGroupHasUnit(lp_h, UnitTransport(lv_u))",
      guard="(UnitIsValid(lv_u) == true)"))
for _n, _f in [("gf_S4UnitCooldown", "UnitGetCooldown(lv_u, lp_link)"),
               ("gf_S4UnitChargesUsed", "UnitGetChargeUsed(lv_u, lp_link)"),
               ("gf_S4UnitChargeRegen", "UnitGetChargeRegen(lv_u, lp_link)")]:
    h(agg(_n, [("string", "lp_link")], "min", _f))
for _n, _f in [("gf_S4AbilChargesUsed", "UnitAbilityGetChargeUsed(lv_u, lp_a, lp_link)"),
               ("gf_S4AbilChargeRegen", "UnitAbilityGetChargeRegen(lv_u, lp_a, lp_link)")]:
    h(agg(_n, [("string", "lp_a"), ("string", "lp_link")], "min", _f))
for _n, _f in [("gf_S4StatusCooldown", "UnitBehaviorGetCooldown(lv_u, lp_b, lp_link)"),
               ("gf_S4StatusChargesUsed", "UnitBehaviorGetChargeUsed(lv_u, lp_b, lp_link)"),
               ("gf_S4StatusChargeRegen", "UnitBehaviorGetChargeRegen(lv_u, lp_b, lp_link)")]:
    h(agg(_n, [("string", "lp_b"), ("string", "lp_link")], "min", _f))
h(agg("gf_S4TrainProgress", [], "max", "UnitGetProgressComplete(lv_u, 1)"))
h(agg("gf_S4Producing", [], "any", "UnitCheckProgressState(lv_u, c_unitProgressTypeTrain, c_unitProgressStateActive)"))
h(agg("gf_S4QueueUsed", [], "sum", "UnitQueueGetProperty(lv_u, c_unitQueuePropertyUsed)", rtype="int"))
h(agg("gf_S4Queued", [("string", "lp_type")], "sum", "UnitTechTreeUnitCount(lv_u, lp_type, c_techCountQueuedOrBetter)", rtype="int"))
h(agg("gf_S4UnitStatusCount", [("string", "lp_b")], "sum", "UnitTechTreeBehaviorCount(lv_u, lp_b, c_techCountCompleteOnly)", rtype="int"))
h(agg("gf_S4UnitUpgradeCount", [("string", "lp_up")], "sum", "UnitTechTreeUpgradeCount(lv_u, lp_up, c_techCountCompleteOnly)", rtype="int"))
h(agg("gf_S4UnderConstruction", [], "any", "libNtve_gf_UnitIsUnderConstruction(lv_u)"))
h(agg("gf_S4HasAddon", [], "any", "UnitAddOnChild(lv_u, 0) != null"))
h(agg("gf_S4ArmyValue", [], "sum", "UnitTypeGetCost(UnitGetType(lv_u), c_unitCostSumMineralsVespene)", rtype="int"))
h(agg("gf_S4ResourcesLeft", [], "sum", "libNtve_gf_UnitGetPropertyResources(lv_u, true)", rtype="int"))
h(agg("gf_S4Invulnerable", [], "any", "libNtve_gf_UnitIsInvulnerable(lv_u)"))
h(raw("gf_S4Firepower", [
    "fixed gf_S4Firepower (unitgroup lp_g) {", "    int lv_i;", "    int lv_n;", "    int lv_w;", "    unit lv_u;",
    "    fixed lv_s;", "    lv_s = 0.0;",
    "    lv_n = UnitGroupCount(lp_g, c_unitCountAll);", "    lv_i = 1;", "    while (lv_i <= lv_n) {",
    "        lv_u = UnitGroupUnit(lp_g, lv_i);", "        if (UnitIsAlive(lv_u) == true) {",
    "            lv_w = 1;", "            while (lv_w <= UnitWeaponCount(lv_u)) {",
    "                if ((UnitWeaponIsEnabled(lv_u, lv_w) == true) && (UnitWeaponPeriod(lv_u, lv_w) > 0.0)) {",
    "                    lv_s = (lv_s + (UnitWeaponDamage(lv_u, lv_w, c_unitAttributeNone, false) / UnitWeaponPeriod(lv_u, lv_w)));",
    "                }", "                lv_w = (lv_w + 1);", "            }", "        }",
    "        lv_i = (lv_i + 1);", "    }", "    return lv_s;", "}"]))
h(agg("gf_S4TotalVitals", [], "sum",
      "UnitGetPropertyFixed(lv_u, c_unitPropLife, c_unitPropCurrent) + UnitGetPropertyFixed(lv_u, c_unitPropShields, c_unitPropCurrent)"))
h(agg("gf_S4Engaging", [], "any", "(UnitOrderCount(lv_u) > 0) && UnitOrderIsAcquired(lv_u, 0)"))
h(agg("gf_S4OrderedWith", [("string", "lp_a")], "any",
      "(UnitOrderCount(lv_u) > 0) && (AbilityCommandGetAbility(OrderGetAbilityCommand(UnitOrder(lv_u, 0))) == lp_a)"))
h(agg("gf_S4RalliedTo", [("point", "lp_p"), ("fixed", "lp_r")], "any",
      "(UnitRallyPointCount(lv_u) > 0) && (DistanceBetweenPoints(UnitRallyPointTargetPoint(lv_u, 1, 1), lp_p) <= lp_r)"))
h(agg("gf_S4StatusSourceIn", [("string", "lp_b"), ("unitgroup", "lp_h")], "any",
      "UnitHasBehavior2(lv_u, lp_b) && UnitGroupHasUnit(lp_h, UnitBehaviorEffectUnit(lv_u, lp_b, c_effectUnitCaster, 0))"))
h(agg("gf_S4StatusSourceSide", [("string", "lp_b"), ("int", "lp_p")], "any",
      "UnitHasBehavior2(lv_u, lp_b) && (UnitBehaviorEffectPlayer(lv_u, lp_b, c_effectUnitCaster, 0) == lp_p)"))
_EH_HEAD = ["    int lv_i;", "    int lv_n;", "    int lv_j;", "    unit lv_u;", "    effecthistory lv_eh;"]
_EH_LOOP = ["    lv_n = UnitGroupCount(lp_g, c_unitCountAll);", "    lv_i = 1;", "    while (lv_i <= lv_n) {",
            "        lv_u = UnitGroupUnit(lp_g, lv_i);", "        if (UnitIsValid(lv_u) == true) {",
            "            lv_eh = UnitEffectHistory(lv_u, 32);", "            lv_j = 1;",
            "            while (lv_j <= EffectHistoryCount(lv_eh)) {"]
_EH_TAIL = ["                lv_j = (lv_j + 1);", "            }", "        }", "        lv_i = (lv_i + 1);", "    }"]
h(raw("gf_S4DamagedBy", ["bool gf_S4DamagedBy (unitgroup lp_g, unitgroup lp_h, fixed lp_within) {", *_EH_HEAD, *_EH_LOOP,
      "                if ((EffectHistoryGetType(lv_eh, lv_j) == c_effectHistoryDamage) && ((GameGetMissionTime() - EffectHistoryGetTime(lv_eh, lv_j)) <= lp_within) && (UnitGroupHasUnit(lp_h, EffectHistoryGetUnitByLocation(lv_eh, lv_j, c_effectUnitCaster)) == true)) {",
      "                    return true;", "                }", *_EH_TAIL, "    return false;", "}"]))
h(raw("gf_S4DamagedWith", ["bool gf_S4DamagedWith (unitgroup lp_g, string lp_link) {", *_EH_HEAD, *_EH_LOOP,
      "                if ((EffectHistoryGetEffect(lv_eh, lv_j, c_effectHistoryEffectRoot) == lp_link) || (EffectHistoryGetWeapon(lv_eh, lv_j) == lp_link) || (EffectHistoryGetAbil(lv_eh, lv_j) == lp_link)) {",
      "                    return true;", "                }", *_EH_TAIL, "    return false;", "}"]))
h(raw("gf_S4DamageAmountFrom", ["int gf_S4DamageAmountFrom (unitgroup lp_g, unitgroup lp_h) {", *_EH_HEAD, "    int lv_s;",
      "    lv_s = 0;", *_EH_LOOP,
      "                if (UnitGroupHasUnit(lp_h, EffectHistoryGetUnitByLocation(lv_eh, lv_j, c_effectUnitCaster)) == true) {",
      "                    lv_s = (lv_s + EffectHistoryGetAmountInt(lv_eh, lv_j, c_effectAmountDamaged, false));",
      "                }", *_EH_TAIL, "    return lv_s;", "}"]))
h(raw("gf_S4IdleCount", [
    "int gf_S4IdleCount (unitgroup lp_g, int lp_p) {", "    int lv_i;", "    int lv_n;", "    int lv_c;", "    unit lv_u;",
    "    unitgroup lv_idle;", "    lv_c = 0;", "    lv_idle = UnitGroupIdle(lp_p, false);",
    "    lv_n = UnitGroupCount(lp_g, c_unitCountAll);", "    lv_i = 1;", "    while (lv_i <= lv_n) {",
    "        lv_u = UnitGroupUnit(lp_g, lv_i);",
    "        if ((UnitIsAlive(lv_u) == true) && (UnitGroupHasUnit(lv_idle, lv_u) == true)) {",
    "            lv_c = (lv_c + 1);", "        }", "        lv_i = (lv_i + 1);", "    }", "    return lv_c;", "}"]))
h(raw("gf_S4Detach", [
    "void gf_S4Detach (unitgroup lp_g, unitgroup lp_h, int lp_n) {", "    int lv_k;", "    unit lv_u;", "    lv_k = 0;",
    "    while ((lv_k < lp_n) && (UnitGroupCount(lp_g, c_unitCountAlive) > 0)) {",
    "        lv_u = UnitGroupRandomUnit(lp_g, c_unitCountAlive);", "        UnitGroupRemove(lp_g, lv_u);",
    "        UnitGroupAdd(lp_h, lv_u);", "        lv_k = (lv_k + 1);", "    }", "}"]))
h(foreach("gf_S4Tag", [("int", "lp_slot"), ("fixed", "lp_v")], ["UnitSetCustomValue(lv_u, lp_slot, lp_v);"]))
h(raw("gf_S4FlankAngle", [
    "fixed gf_S4FlankAngle (point lp_a, point lp_x, point lp_b) {", "    fixed lv_d;",
    "    lv_d = AbsF((AngleBetweenPoints(lp_x, lp_a) - AngleBetweenPoints(lp_x, lp_b)));",
    "    if (lv_d > 180.0) {", "        lv_d = (360.0 - lv_d);", "    }", "    return lv_d;", "}"]))
h(raw("gf_S4AttachRegion", [
    "void gf_S4AttachRegion (region lp_r, unitgroup lp_g) {",
    "    if ((RegionGetAttachUnit(lp_r) == null) || (UnitIsAlive(RegionGetAttachUnit(lp_r)) == false)) {",
    "        if (UnitGroupCount(lp_g, c_unitCountAlive) > 0) {",
    "            RegionAttachToUnit(lp_r, UnitGroupUnit(lp_g, 1), Point(0.0, 0.0));", "        }", "    }", "}"]))
h(raw("gf_S4Build", [
    "void gf_S4Build (unitgroup lp_asset, string lp_type, int lp_p, point lp_c, fixed lp_r) {",
    "    libNtve_gf_CreateUnitsWithDefaultFacing(1, lp_type, c_unitCreateConstruct, lp_p, UnitTypePlacementFromPoint(lp_type, lp_p, lp_c, lp_r));",
    "    UnitGroupAddUnitGroup(lp_asset, UnitLastCreatedGroup());", "}"]))
h(raw("gf_S4Replace", [
    "void gf_S4Replace (unitgroup lp_g, string lp_type) {", "    unitgroup lv_old;", "    int lv_i;", "    int lv_n;",
    "    unit lv_u;", "    lv_old = UnitGroupCopy(lp_g);", "    UnitGroupClear(lp_g);",
    "    lv_n = UnitGroupCount(lv_old, c_unitCountAll);", "    lv_i = 1;", "    while (lv_i <= lv_n) {",
    "        lv_u = UnitGroupUnit(lv_old, lv_i);", "        if (UnitIsAlive(lv_u) == true) {",
    "            libNtve_gf_ReplaceUnit(lv_u, lp_type, 0);", "            UnitGroupAdd(lp_g, libNtve_gf_LastReplacedUnit());",
    "        }", "        lv_i = (lv_i + 1);", "    }", "}"]))
APPLY = {}  # DSL action -> (helper, extra param types)
for _hn, _extra, _stmt in [
    ("gf_S4ForceKill", [], "UnitKill(lv_u);"),
    ("gf_S4ForceRemove", [], "UnitRemove(lv_u);"),
    ("gf_S4ForceOwner", [("int", "lp_p")], "UnitSetOwner(lv_u, lp_p, true);"),
    ("gf_S4ForceTeleport", [("point", "lp_p")], "UnitSetPosition(lv_u, lp_p, false);"),
    ("gf_S4ForceFace", [("point", "lp_p")], "libNtve_gf_MakeUnitFacePoint(lv_u, lp_p, 0.0);"),
    ("gf_S4ForcePause", [("bool", "lp_on")], "libNtve_gf_PauseUnit(lv_u, lp_on);"),
    ("gf_S4ForceHide", [("bool", "lp_on")], "libNtve_gf_ShowHideUnit(lv_u, (lp_on == false));"),
    ("gf_S4ForceSleep", [("bool", "lp_on")], "libNtve_gf_SleepUnit(lv_u, lp_on);"),
    ("gf_S4ShareVision", [("int", "lp_p")], "libNtve_gf_ShareVisionofUnit(lv_u, true, lp_p);"),
    ("gf_S4AbilityEnable", [("string", "lp_a"), ("bool", "lp_on")], "UnitAbilityEnable(lv_u, lp_a, lp_on);"),
    ("gf_S4AbilityLevel", [("string", "lp_a"), ("int", "lp_n")], "UnitAbilityChangeLevel(lv_u, lp_a, lp_n);"),
    ("gf_S4StatusAddPlayer", [("string", "lp_b"), ("int", "lp_p"), ("int", "lp_n")], "UnitBehaviorAddPlayer(lv_u, lp_b, lp_p, lp_n);"),
    ("gf_S4StatusRemovePlayer", [("string", "lp_b"), ("int", "lp_p"), ("int", "lp_n")], "UnitBehaviorRemovePlayer(lv_u, lp_b, lp_p, lp_n);"),
    ("gf_S4StatusStrip", [("int", "lp_cat")], "UnitBehaviorRemoveCategory(lv_u, lp_cat);"),
    ("gf_S4StatusDuration", [("string", "lp_b"), ("fixed", "lp_s")], "UnitBehaviorSetDurationRemaining(lv_u, lp_b, lp_s);"),
    ("gf_S4StatusDurationTotal", [("string", "lp_b"), ("fixed", "lp_s")], "UnitBehaviorSetDuration(lv_u, lp_b, lp_s);"),
    ("gf_S4StatusStacks", [("string", "lp_b"), ("int", "lp_n")], "libNtve_gf_SetBehaviorCount(lv_u, lp_b, lv_u, lp_n);"),
    ("gf_S4StatusTransfer", [("unit", "lp_dst"), ("string", "lp_b")], "UnitBehaviorTransfer(lv_u, lp_dst, lp_b, 1);"),
    ("gf_S4ClearCooldowns", [], "UnitClearCooldowns(lv_u, false);"),
    ("gf_S4UnitCooldownSet", [("string", "lp_link"), ("fixed", "lp_s")], "UnitModifyCooldown(lv_u, lp_link, lp_s, c_cooldownOperationSet);"),
    ("gf_S4UnitCooldownClear", [("string", "lp_link")], "libNtve_gf_UnitRemoveCooldown(lv_u, lp_link);"),
    ("gf_S4UnitChargesSpend", [("string", "lp_link"), ("fixed", "lp_n")], "UnitAddChargeUsed(lv_u, lp_link, lp_n);"),
    ("gf_S4UnitChargesRestore", [("string", "lp_link")], "libNtve_gf_UnitRemoveChargeUsed(lv_u, lp_link);"),
    ("gf_S4UnitChargeRegenFull", [("string", "lp_link"), ("fixed", "lp_s")], "UnitAddChargeRegenFull(lv_u, lp_link, lp_s);"),
    ("gf_S4UnitChargeRegenLeft", [("string", "lp_link"), ("fixed", "lp_s")], "UnitAddChargeRegenRemaining(lv_u, lp_link, lp_s);"),
    ("gf_S4AbilCooldownAdd", [("string", "lp_a"), ("string", "lp_link"), ("fixed", "lp_s")], "UnitAbilityAddCooldown(lv_u, lp_a, lp_link, lp_s);"),
    ("gf_S4AbilCooldownClear", [("string", "lp_a"), ("string", "lp_link")], "libNtve_gf_UnitAbilityRemoveCooldown(lv_u, lp_a, lp_link);"),
    ("gf_S4AbilChargesSpend", [("string", "lp_a"), ("string", "lp_link"), ("fixed", "lp_n")], "UnitAbilityAddChargeUsed(lv_u, lp_a, lp_link, lp_n);"),
    ("gf_S4AbilChargesRestore", [("string", "lp_a"), ("string", "lp_link")], "libNtve_gf_UnitAbilityRemoveChargeUsed(lv_u, lp_a, lp_link);"),
    ("gf_S4AbilChargeRegenFull", [("string", "lp_a"), ("string", "lp_link"), ("fixed", "lp_s")], "UnitAbilityAddChargeRegenFull(lv_u, lp_a, lp_link, lp_s);"),
    ("gf_S4AbilChargeRegenLeft", [("string", "lp_a"), ("string", "lp_link"), ("fixed", "lp_s")], "UnitAbilityAddChargeRegenRemaining(lv_u, lp_a, lp_link, lp_s);"),
    ("gf_S4AbilReset", [("string", "lp_a")], "UnitAbilityReset(lv_u, AbilityCommand(lp_a, 0), c_spendLocationAll);"),
    ("gf_S4StatusCooldownAdd", [("string", "lp_b"), ("string", "lp_link"), ("fixed", "lp_s")], "UnitBehaviorAddCooldown(lv_u, lp_b, lp_link, lp_s);"),
    ("gf_S4StatusCooldownClear", [("string", "lp_b"), ("string", "lp_link")], "libNtve_gf_UnitBehaviorRemoveCooldown(lv_u, lp_b, lp_link);"),
    ("gf_S4StatusChargesSpend", [("string", "lp_b"), ("string", "lp_link"), ("fixed", "lp_n")], "UnitBehaviorAddChargeUsed(lv_u, lp_b, lp_link, lp_n);"),
    ("gf_S4StatusChargesRestore", [("string", "lp_b"), ("string", "lp_link")], "libNtve_gf_UnitBehaviorRemoveChargeUsed(lv_u, lp_b, lp_link);"),
    ("gf_S4StatusChargeRegenFull", [("string", "lp_b"), ("string", "lp_link"), ("fixed", "lp_s")], "UnitBehaviorAddChargeRegenFull(lv_u, lp_b, lp_link, lp_s);"),
    ("gf_S4StatusChargeRegenLeft", [("string", "lp_b"), ("string", "lp_link"), ("fixed", "lp_s")], "UnitBehaviorAddChargeRegenRemaining(lv_u, lp_b, lp_link, lp_s);"),
    ("gf_S4ProgressSet", [("int", "lp_pct")], "UnitSetProgressComplete(lv_u, c_unitProgressTypeConstruct, lp_pct);"),
    ("gf_S4ProgressPause", [], "UnitSetProgressStage(lv_u, c_unitProgressTypeConstruct, c_unitProgressStagePause);"),
    ("gf_S4VitalSet", [("int", "lp_prop"), ("fixed", "lp_v")], "UnitSetPropertyFixed(lv_u, lp_prop, lp_v);"),
    ("gf_S4StateSet", [("int", "lp_state"), ("bool", "lp_on")], "UnitSetState(lv_u, lp_state, lp_on);"),
    ("gf_S4DamageScale", [("int", "lp_dir"), ("int", "lp_opt")], "libNtve_gf_ChangeUnitDamage(lv_u, lp_dir, lp_opt);"),
    ("gf_S4SetInvulnerable", [("bool", "lp_on")], "libNtve_gf_MakeUnitInvulnerable(lv_u, lp_on);"),
    ("gf_S4Uncommandable", [("bool", "lp_on")], "libNtve_gf_MakeUnitUncommandable(lv_u, lp_on);"),
    ("gf_S4WeaponAdd", [("string", "lp_w"), ("string", "lp_turret")], "UnitWeaponAdd(lv_u, lp_w, lp_turret);"),
    ("gf_S4WeaponRemove", [("string", "lp_w")], "UnitWeaponRemove(lv_u, lp_w);"),
]:
    h(foreach(_hn, _extra, [_stmt]))

# ------------------------------------------------------------------ events
def ident(lo, e, i=0):
    return lo._event_identity_guards(nm(e, i))


@lower_ev("property_changed")
def _(lo, e, gt):
    return [f"    TriggerAddEventPlayerPropChange({gt}, {side(lo, e, 0)}, {K(PLAYER_PROPS[voc(e, 1, PLAYER_PROPS)])});"], []


@lower_ev("upgrade_changed")
def _(lo, e, gt):
    return [f"    TriggerAddEventUpgradeLevelChanged({gt}, {side(lo, e, 0)});"], [f"EventUpgradeName() == {gs(st(e, 1))}"]


@lower_ev("side_left")
def _(lo, e, gt):
    return [f"    TriggerAddEventPlayerLeft({gt}, {side(lo, e, 0)}, {K('c_gameResultUndecided')});"], []


@lower_ev("ability_stage")
def _(lo, e, gt):
    stage = K(ABIL_STAGES[voc(e, 2, ABIL_STAGES)])
    return [f"    TriggerAddEventUnitAbility({gt}, null, AbilityCommand({gs(st(e, 1))}, 0), {stage}, false);"], ident(lo, e)


@lower_ev("autocast_changed")
def _(lo, e, gt):
    ch = K(AUTOCAST[voc(e, 2, AUTOCAST)])
    return [f"    TriggerAddEventUnitAbilityAutoCastChange({gt}, null, AbilityCommand({gs(st(e, 1))}, 0), {ch}, false);"], ident(lo, e)


def _status_class(change):
    def reg(lo, e, gt):
        cat = K(BEHAVIOR_CATEGORIES[voc(e, 1, BEHAVIOR_CATEGORIES)])
        return [f"    TriggerAddEventUnitBehaviorChangeFromCategory({gt}, null, {cat}, {K(change)});"], ident(lo, e)
    return reg


lower_ev("status_class_gained")(_status_class("c_unitBehaviorChangeCreate"))
lower_ev("status_class_lost")(_status_class("c_unitBehaviorChangeDestroy"))


@lower_ev("damage_absorbed")
def _(lo, e, gt):
    return [f"    TriggerAddEventUnitDamageAbsorbed({gt}, null, {gs(st(e, 1))});"], ident(lo, e)


@lower_ev("research_done")
def _(lo, e, gt):
    return ([f"    TriggerAddEventUnitResearchProgress({gt}, null, {K('c_unitProgressStageComplete')});"],
            ident(lo, e) + [f"libNtve_gf_TriggeringProgressUpgrade() == {gs(st(e, 1))}"])


@lower_ev("trained")
def _(lo, e, gt):
    return ([f"    TriggerAddEventUnitTrainProgress({gt}, null, {K('c_unitProgressStageComplete')});"],
            ident(lo, e) + [f"libNtve_gf_TriggeringProgressUnitType() == {gs(st(e, 1))}"])


@lower_ev("vital_changed")
def _(lo, e, gt):
    return [f"    TriggerAddEventUnitProperty({gt}, null, {K(VITAL_PROPS[voc(e, 1, VITAL_PROPS)])});"], ident(lo, e)


@lower_ev("produced")
def _(lo, e, gt):
    return ([f"    TriggerAddEventUnitCreated({gt}, null, null, null);"],
            [f"UnitGroupHasUnit({lo._group(nm(e, 0))}, EventUnit()) == true",
             f"UnitGetType(EventUnitCreatedUnit()) == {gs(st(e, 1))}"])


@lower_ev("unit_healed")
def _(lo, e, gt):
    return [f"    TriggerAddEventUnitHealed({gt}, null, {K('c_unitVitalAny')}, null);"], ident(lo, e)


@lower_ev("loaded")
def _(lo, e, gt):
    return [f"    TriggerAddEventUnitCargo({gt}, null, true);"], ident(lo, e)


@lower_ev("unloaded")
def _(lo, e, gt):
    return [f"    TriggerAddEventUnitCargo({gt}, null, false);"], ident(lo, e)


@lower_ev("acquired_target")
def _(lo, e, gt):
    return [f"    TriggerAddEventUnitAcquiredTarget({gt}, null);"], ident(lo, e)


@lower_ev("attack_started")
def _(lo, e, gt):
    return [f"    TriggerAddEventUnitStartedAttack2({gt}, null, null);"], ident(lo, e)
AMOUNT = {"property_changed": "EventPlayerPropertyChangeFixed()", "upgrade_changed": "IntToFixed(EventUpgradeLevelDelta())",
          "vital_changed": "EventUnitPropertyChangeFixed()", "unit_healed": "EventUnitHealAmount()",
          "damage_absorbed": "EventUnitDamageAbsorbed()"}


def evname(lo):
    return lo._event_ctx.name if lo._event_ctx is not None else None


@lower_fn("event_ability_is")
def _(lo, e):
    return f"(AbilityCommandGetAbility(EventUnitAbility()) == {gs(st(e, 0))})"


@lower_fn("event_stage_is")
def _(lo, e):
    return f"(EventUnitAbilityStage() == {K(ABIL_STAGES[voc(e, 0, ABIL_STAGES)])})"


@lower_fn("event_other_in")
def _(lo, e):
    return f"(UnitGroupHasUnit({lo._group(nm(e, 0))}, EventUnitAbilityOtherUnit()) == true)"


@lower_fn("event_cargo_in")
def _(lo, e):
    return f"(UnitGroupHasUnit({lo._group(nm(e, 0))}, EventUnitCargo()) == true)"


@lower_fn("event_damage")
def _(lo, e):
    return DAMAGE_KINDS[voc(e, 0, DAMAGE_KINDS)]


@lower_fn("event_leeched")
def _(lo, e):
    return f"EventUnitDamageVitalsLeeched({K(VITALS[voc(e, 0, VITALS)])})"


@lower_fn("event_source_at")
def _(lo, e):
    return f"RegionContainsPoint({lo._region(nm(e, 0))}, EventUnitDamageSourcePoint())"


@lower_fn("event_weapon_is")
def _(lo, e):
    return f"(EventUnitGetWeapon() == {gs(st(e, 0))})"


@lower_fn("event_death_is")
def _(lo, e):
    return f"(EventUnitDamageDeathCheck({K(DEATH_TYPES[voc(e, 0, DEATH_TYPES)])}) == true)"


@lower_fn("event_effect_is")
def _(lo, e):
    src = "EventUnitHealEffect()" if evname(lo) == "unit_healed" else "EventUnitDamageEffect()"
    return f"({src} == {gs(st(e, 0))})"


_SIDE_SRC = {"unit_healed": "EventUnitHealLaunchPlayer()", "unit_damaged": "EventUnitDamageSourcePlayer()",
             "unit_died": "libNtve_gf_KillingPlayer()"}


@lower_fn("event_source_side")
def _(lo, e):
    return f"({_SIDE_SRC[evname(lo)]} == {side(lo, e, 0)})"


@lower_fn("event_vital_is")
def _(lo, e):
    return f"(EventUnitHealVital() == {K(VITALS[voc(e, 0, VITALS)])})"


@lower_fn("event_object_is")
def _(lo, e):
    return f"(EventUnitProgressObjectType() == {gs(st(e, 0))})"


@lower_fn("event_product_in")
def _(lo, e):
    return f"(UnitGroupHasUnit({lo._group(nm(e, 0))}, EventUnitProgressUnit()) == true)"


@lower_fn("event_created_by")
def _(lo, e):
    return f"(EventUnitCreatedAbil() == {gs(st(e, 0))})"


@lower_fn("event_created_by_status")
def _(lo, e):
    return f"(EventUnitCreatedBehavior() == {gs(st(e, 0))})"


def emit_event_amount(lo) -> Optional[str]:
    return AMOUNT.get(evname(lo))


# ------------------------------------------------------------------ memory / time
@lower_fn("recall")
def _(lo, e):
    return f"DataTableGetFixed(true, {key(lo, e)})"


@lower_fn("tallied")
def _(lo, e):
    return f"DataTableGetInt(true, {key(lo, e)})"


@lower_fn("known")
def _(lo, e):
    return f"DataTableValueExists(true, {key(lo, e)})"


@lower_fn("marked")
def _(lo, e):
    return f"DataTableGetBool(true, {key(lo, e)})"


@lower_fn("count_snapshot")
def _(lo, e):
    return f"UnitGroupCount(DataTableGetUnitGroup(true, {key(lo, e)}), c_unitCountAlive)"


@lower_fn("snapshot_lost")
def _(lo, e):
    return (f"(DataTableGetInt(true, {snapshot_size_key(lo, e)}) - "
            f"UnitGroupCount(DataTableGetUnitGroup(true, {key(lo, e)}), c_unitCountAlive))")


@lower_fn("remembered_alive")
def _(lo, e):
    return f"(UnitIsAlive(DataTableGetUnit(true, {key(lo, e)})) == true)"


@lower_fn("remembered_in")
def _(lo, e):
    return f"(UnitGroupHasUnit({lo._group(nm(e, 0))}, DataTableGetUnit(true, {key(lo, e, 1)})) == true)"


@lower_fn("near_remembered")
def _(lo, e):
    return f"(DistanceBetweenPoints({center(lo, nm(e, 0))}, DataTableGetPoint(true, {key(lo, e, 1)})) <= {fx(numv(e, 2))})"


@lower_fn("chosen")
def _(lo, e):
    return f"(DataTableGetString(true, {key(lo, e)}) == {gs(st(e, 1))})"


@lower_fn("count_tagged")
def _(lo, e):
    return (f"UnitGroupCount(libNtve_gf_UnitsInUnitGroupWithCustomValue({lo._group(nm(e, 0))}, "
            f"{lo.ext_state.slot(st(e, 1))}, {fx(numv(e, 2))}), c_unitCountAlive)")


@lower_fn("window_held")
def _(lo, e):
    return f"(TimerIsPaused({lo.ext_timer(e)}) == true)"


# ------------------------------------------------------------------ relations
def _rel(relation):
    def lower(lo, e):
        return f"libNtve_gf_PlayerIsEnemy({side(lo, e, 0)}, {side(lo, e, 1)}, {K(relation)})"
    return lower


lower_fn("hostile")(_rel("libNtve_ge_PlayerRelation_Enemy"))
lower_fn("hostile_mutual")(_rel("libNtve_ge_PlayerRelation_EnemyMutual"))
lower_fn("allied")(_rel("libNtve_ge_PlayerRelation_Ally"))


@lower_fn("side_size")
def _(lo, e):
    gv = lo.ext_state.side_groups.get(voc(e, 0, SIDES))
    return f"PlayerGroupCount({gv})" if gv else "1"


@lower_fn("bearing")
def _(lo, e):
    return f"AngleBetweenPoints({center(lo, nm(e, 0))}, {center(lo, nm(e, 1))})"


@lower_fn("flank_angle")
def _(lo, e):
    need(lo, "gf_S4FlankAngle")
    return f"gf_S4FlankAngle({center(lo, nm(e, 0))}, {center(lo, nm(e, 1))}, {center(lo, nm(e, 2))})"


@lower_fn("pathing_is")
def _(lo, e):
    return f"(PathingType({center(lo, nm(e, 0))}) == {K(PATHING[voc(e, 1, PATHING)])})"


@lower_fn("can_reach")
def _(lo, e):
    f, x = nm(e, 0), nm(e, 1)
    if lo._world_type(x) == "region":
        need(lo, "gf_S4CanReachPoint")
        return f"gf_S4CanReachPoint({lo._group(f)}, {center(lo, x)})"
    need(lo, "gf_S4CanReach")
    return f"gf_S4CanReach({lo._group(f)}, {lo._group(x)})"


def unit_filter_literal(req, exc) -> str:
    names = {**TARGET_FILTER_BITS, **FILTER_ALLIANCE_BITS}
    exc = list(exc) + [x for x in ("Missile", "Dead", "Hidden") if x not in req and x not in exc]

    def words(ns):
        lo_, hi = 0, 0
        for n in ns:
            b = names[n]
            if b < 32:
                lo_ |= 1 << b
            else:
                hi |= 1 << (b - 32)
        return lo_, hi

    rl, rh = words(req)
    el, eh = words(exc)
    return f"UnitFilter({rl}, {rh}, {el}, {eh})"


@lower_fn("count_matching_vs")
def _(lo, e):
    req, exc, errors = filter_masks(st(e, 2))
    if errors:
        err("; ".join(errors))
    need(lo, "gf_S4CountMatchVs")
    return f"gf_S4CountMatchVs({lo._group(nm(e, 0))}, {side(lo, e, 1)}, {unit_filter_literal(req, exc)})"


@lower_fn("can_attack")
def _(lo, e):
    need(lo, "gf_S4CanAttack")
    return f"gf_S4CanAttack({lo._group(nm(e, 0))}, {lo._group(nm(e, 1))})"


@lower_fn("count_owned")
def _(lo, e):
    return f"UnitGroupCount(UnitGroupFilterPlayer({lo._group(nm(e, 0))}, {side(lo, e, 1)}, 0), c_unitCountAlive)"


# ------------------------------------------------------------------ perception
@lower_fn("creep_adjacent")
def _(lo, e):
    return f"CreepAdjacent({center(lo, nm(e, 0))})"


@lower_fn("powered")
def _(lo, e):
    need(lo, "gf_S4AllPowered")
    return f"gf_S4AllPowered({lo._group(nm(e, 0))})"


@lower_fn("powered_by")
def _(lo, e):
    need(lo, "gf_S4PoweredBy")
    return f"gf_S4PoweredBy({lo._group(nm(e, 0))}, {lo._group(nm(e, 1))})"


# ------------------------------------------------------------------ queries
@lower_fn("supply")
def _(lo, e):
    return f"PlayerGetPropertyFixed({side(lo, e, 0)}, {K(SUPPLY[voc(e, 1, SUPPLY)])})"


@lower_fn("race_is")
def _(lo, e):
    return f"(PlayerRace({side(lo, e, 0)}) == {gs(st(e, 1))})"


@lower_fn("score")
def _(lo, e):
    return f"PlayerScoreValueGetAsFixed({side(lo, e, 0)}, {gs(st(e, 1))})"


@lower_fn("score_count")
def _(lo, e):
    return f"PlayerScoreValueGetAsInt({side(lo, e, 0)}, {gs(st(e, 1))})"


@lower_fn("side_active")
def _(lo, e):
    return f"(PlayerStatus({side(lo, e, 0)}) == {K('c_playerStatusActive')})"


@lower_fn("status_count")
def _(lo, e):
    return f"TechTreeBehaviorCount({side(lo, e, 0)}, {gs(st(e, 1))}, {K('c_techCountCompleteOnly')})"


@lower_fn("ability_count")
def _(lo, e):
    return f"TechTreeAbilityCount({side(lo, e, 0)}, {gs(st(e, 1))}, {K('c_techCountCompleteOnly')})"


def _grp_helper(helper):
    def lower(lo, e):
        need(lo, helper)
        extra = "".join(", " + gs(st(e, i)) for i in range(1, len(e.args)))
        return f"{helper}({lo._group(nm(e, 0))}{extra})"
    return lower


for _name, _helper in [
    ("queued", "gf_S4Queued"),
    ("unit_status_count", "gf_S4UnitStatusCount"),
    ("unit_upgrade_count", "gf_S4UnitUpgradeCount"),
    ("has_ability", "gf_S4HasAbil"),
    ("ability_enabled", "gf_S4AbilEnabled"),
    ("ability_level", "gf_S4AbilLevel"),
    ("summoned_with", "gf_S4SummonedWith"),
    ("shield_left", "gf_S4ShieldLeft"),
    ("status_fraction_left", "gf_S4StatusFractionLeft"),
    ("status_active", "gf_S4StatusActive"),
    ("carried", "gf_S4Carried"),
    ("cooldown_left", "gf_S4UnitCooldown"),
    ("charges_used", "gf_S4UnitChargesUsed"),
    ("charge_regen_left", "gf_S4UnitChargeRegen"),
    ("ability_charges_used", "gf_S4AbilChargesUsed"),
    ("ability_charge_regen_left", "gf_S4AbilChargeRegen"),
    ("status_cooldown_left", "gf_S4StatusCooldown"),
    ("status_charges_used", "gf_S4StatusChargesUsed"),
    ("status_charge_regen_left", "gf_S4StatusChargeRegen"),
    ("producing", "gf_S4Producing"),
    ("train_progress", "gf_S4TrainProgress"),
    ("queue_used", "gf_S4QueueUsed"),
    ("under_construction", "gf_S4UnderConstruction"),
    ("has_addon", "gf_S4HasAddon"),
    ("airborne", "gf_S4AnyAir"),
    ("army_value", "gf_S4ArmyValue"),
    ("resources_left", "gf_S4ResourcesLeft"),
    ("invulnerable", "gf_S4Invulnerable"),
    ("firepower", "gf_S4Firepower"),
    ("engaging", "gf_S4Engaging"),
    ("ordered_with", "gf_S4OrderedWith"),
    ("damaged_with", "gf_S4DamagedWith"),
]:
    lower_fn(_name)(_grp_helper(_helper))


@lower_fn("tech_allowed")
def _(lo, e):
    p, kind, name = side(lo, e, 0), voc(e, 1, TECH_KINDS), gs(st(e, 2))
    if kind == "ability":
        return f"TechTreeAbilityIsAllowed({p}, AbilityCommand({name}, 0))"
    return f"Tech{'Tree'}{kind.capitalize()}IsAllowed({p}, {name})"


@lower_fn("summoned_by")
def _(lo, e):
    need(lo, "gf_S4SummonedBy")
    return f"gf_S4SummonedBy({lo._group(nm(e, 0))}, {lo._group(nm(e, 1))})"


@lower_fn("cargo_count")
def _(lo, e):
    need(lo, "gf_S4CargoValue")
    return f"gf_S4CargoValue({lo._group(nm(e, 0))}, {K('c_unitCargoUnitCount')})"


@lower_fn("cargo_space")
def _(lo, e):
    need(lo, "gf_S4CargoValue")
    return f"gf_S4CargoValue({lo._group(nm(e, 0))}, {K('c_unitCargoSpaceFree')})"


@lower_fn("carried_by")
def _(lo, e):
    need(lo, "gf_S4CarriedBy")
    return f"gf_S4CarriedBy({lo._group(nm(e, 0))}, {lo._group(nm(e, 1))})"


@lower_fn("state")
def _(lo, e):
    need(lo, "gf_S4AnyState")
    return f"gf_S4AnyState({lo._group(nm(e, 0))}, {K(UNIT_STATES[voc(e, 1, UNIT_STATES)])})"


@lower_fn("combat_power")
def _(lo, e):
    """firepower x (life + shields). `strength` stays a strategic-only predicate:
    the negative corpus uses it as the canonical non-groundable metric."""
    need(lo, "gf_S4Firepower", "gf_S4TotalVitals")
    g = lo._group(nm(e, 0))
    return f"(gf_S4Firepower({g}) * gf_S4TotalVitals({g}))"


@lower_fn("rallied_to")
def _(lo, e):
    need(lo, "gf_S4RalliedTo")
    c, r = lo._region_geom(nm(e, 1))
    return f"gf_S4RalliedTo({lo._group(nm(e, 0))}, {c}, {r})"


@lower_fn("damaged_by")
def _(lo, e):
    need(lo, "gf_S4DamagedBy")
    return f"gf_S4DamagedBy({lo._group(nm(e, 0))}, {lo._group(nm(e, 1))}, {fx(numv(e, 2))})"


@lower_fn("damage_from")
def _(lo, e):
    need(lo, "gf_S4DamageAmountFrom")
    return f"gf_S4DamageAmountFrom({lo._group(nm(e, 0))}, {lo._group(nm(e, 1))})"


@lower_fn("status_source_in")
def _(lo, e):
    need(lo, "gf_S4StatusSourceIn")
    return f"gf_S4StatusSourceIn({lo._group(nm(e, 0))}, {gs(st(e, 1))}, {lo._group(nm(e, 2))})"


@lower_fn("status_source_side")
def _(lo, e):
    need(lo, "gf_S4StatusSourceSide")
    return f"gf_S4StatusSourceSide({lo._group(nm(e, 0))}, {gs(st(e, 1))}, {side(lo, e, 2)})"


@lower_fn("order_rejected")
def _(lo, e):
    return f"({lo.ext_state.rejected_flag(nm(e, 0))} == true)"


@lower_fn("idle_count")
def _(lo, e):
    need(lo, "gf_S4IdleCount")
    return f"gf_S4IdleCount({lo._group(nm(e, 0))}, {lo.ext_owner(nm(e, 0))})"


# ------------------------------------------------------------------ actions: memory / time / env
@lower_act("remember")
def _(lo, c, p):
    return [p + f"DataTableSetFixed(true, {key(lo, c)}, {numexpr(lo, _arg(c, 1))});"]


@lower_act("tally")
def _(lo, c, p):
    k = key(lo, c)
    return [p + f"DataTableSetInt(true, {k}, (DataTableGetInt(true, {k}) + {ix(numv(c, 1))}));"]


@lower_act("forget")
def _(lo, c, p):
    return [p + f"DataTableValueRemove(true, {key(lo, c)});",
            p + f"DataTableValueRemove(true, {snapshot_size_key(lo, c)});"]


@lower_act("mark")
def _(lo, c, p):
    return [p + f"DataTableSetBool(true, {key(lo, c)}, true);"]


@lower_act("unmark")
def _(lo, c, p):
    return [p + f"DataTableSetBool(true, {key(lo, c)}, false);"]


@lower_act("snapshot")
def _(lo, c, p):
    g = lo._group(nm(c, 1))
    return [p + f"DataTableSetUnitGroup(true, {key(lo, c)}, UnitGroupCopy({g}));",
            p + f"DataTableSetInt(true, {snapshot_size_key(lo, c)}, UnitGroupCount({g}, c_unitCountAlive));"]


@lower_act("remember_event_unit")
def _(lo, c, p):
    role = voc(c, 1, REACT_ROLES)
    unit = "EventUnit()" if role == "subject" else lo._event_unit_expr("source")
    return [p + f"DataTableSetUnit(true, {key(lo, c)}, {unit});"]


@lower_act("remember_position")
def _(lo, c, p):
    return [p + f"DataTableSetPoint(true, {key(lo, c)}, {center(lo, nm(c, 1))});"]


@lower_act("choose")
def _(lo, c, p):
    return [p + f"DataTableSetString(true, {key(lo, c)}, {gs(st(c, 1))});"]


@lower_act("tag")
def _(lo, c, p):
    need(lo, "gf_S4Tag")
    return [p + f"gf_S4Tag({lo._group(nm(c, 0))}, {lo.ext_state.slot(st(c, 1))}, {fx(numv(c, 2))});"]


@lower_act("hold_window")
def _(lo, c, p):
    return [p + f"TimerPause({lo.ext_timer(c)}, true);"]


@lower_act("resume_window")
def _(lo, c, p):
    return [p + f"TimerPause({lo.ext_timer(c)}, false);"]


@lower_act("restart_window")
def _(lo, c, p):
    return [p + f"TimerRestart({lo.ext_timer(c)});"]


@lower_act("no_fly")
def _(lo, c, p):
    cc, r = lo._region_geom(nm(c, 0))
    return [p + f"PathAddNoFlyZone({cc}, {r}, ({r} * 1.5));"]


@lower_act("clear_no_fly")
def _(lo, c, p):
    return [p + f"PathRemoveNoFlyZonesInRegion({lo._region(nm(c, 0))});"]


@lower_act("reveal")
def _(lo, c, p):
    return [p + f"VisRevealArea({side(lo, c, 0)}, {lo._region(nm(c, 1))}, {fx(numv(c, 2))}, false);"]


@lower_act("reveal_while")
def _(lo, c, p):
    gv = lo.ext_state.revealer_for(lo._current_phase, c)
    return [p + f"VisRevealerCreate({side(lo, c, 0)}, {lo._region(nm(c, 1))});",
            p + f"{gv} = VisRevealerLastCreated();"]


@lower_act("recenter")
def _(lo, c, p):
    return [p + f"RegionSetCenter({lo._region(nm(c, 0))}, {center(lo, nm(c, 1))});"]


@lower_act("transfer")
def _(lo, c, p):
    f, g = lo.ext_static_group(nm(c, 0)), lo.ext_static_group(nm(c, 1))
    return [p + f"libNtve_gf_AddUnitGroupToUnitGroup({f}, {g});", p + f"UnitGroupClear({f});"]


@lower_act("detach")
def _(lo, c, p):
    need(lo, "gf_S4Detach")
    f, g = lo.ext_static_group(nm(c, 0)), lo.ext_static_group(nm(c, 2))
    return [p + f"gf_S4Detach({f}, {g}, {ix(numv(c, 1))});"]


@lower_act("release")
def _(lo, c, p):
    return [p + f"UnitGroupRemoveUnitGroup({lo.ext_static_group(nm(c, 0))}, {lo._group(nm(c, 1))});"]


# ------------------------------------------------------------------ actions: rewrites
def _apply(helper, *argfmt):
    """argfmt items: 'side', 'point', 'str', 'num', 'int', 'bool', 'cat', 'state', 'vital_prop',
    'dmgdir', 'dmgopt', 'unit1' (first unit of a group)."""
    def lower(lo, c, p):
        need(lo, helper)
        out = [lo._group(nm(c, 0))]
        for i, kind in enumerate(argfmt, 1):
            if kind == "side":
                out.append(side(lo, c, i))
            elif kind == "point":
                out.append(center(lo, nm(c, i)))
            elif kind == "str":
                out.append(gs(st(c, i)))
            elif kind == "num":
                out.append(fx(numv(c, i)))
            elif kind == "int":
                out.append(ix(numv(c, i)))
            elif kind == "bool":
                out.append("true" if boo(c, i) else "false")
            elif kind == "cat":
                out.append(K(BEHAVIOR_CATEGORIES[voc(c, i, BEHAVIOR_CATEGORIES)]))
            elif kind == "state":
                out.append(K(UNIT_STATES[voc(c, i, UNIT_STATES)]))
            elif kind == "vital_prop":
                out.append(K(VITAL_PROPS[voc(c, i, VITAL_PROPS)]))
            elif kind == "unit1":
                out.append(f"UnitGroupUnit({lo._group(nm(c, i))}, 1)")
            else:
                raise AssertionError(kind)
        return [p + f"{helper}({', '.join(out)});"]
    return lower

for _name, _helper, _fmt in [
    ("force_kill", "gf_S4ForceKill", ()),
    ("force_remove", "gf_S4ForceRemove", ()),
    ("force_owner", "gf_S4ForceOwner", ("side",)),
    ("rescue", "gf_S4ForceOwner", ("side",)),
    ("force_teleport", "gf_S4ForceTeleport", ("point",)),
    ("force_face", "gf_S4ForceFace", ("point",)),
    ("force_pause", "gf_S4ForcePause", ("bool",)),
    ("force_hide", "gf_S4ForceHide", ("bool",)),
    ("force_sleep", "gf_S4ForceSleep", ("bool",)),
    ("force_replace", "gf_S4Replace", ("str",)),
    ("force_disable", "gf_S4AbilityEnable", ("str",)),
    ("force_status", "gf_S4StatusAddPlayer", ("str", "side", "int")),
    ("force_status_off", "gf_S4StatusRemovePlayer", ("str", "side", "int")),
    ("strip_status", "gf_S4StatusStrip", ("cat",)),
    ("force_status_remaining", "gf_S4StatusDuration", ("str", "num")),
    ("force_status_duration", "gf_S4StatusDurationTotal", ("str", "num")),
    ("force_status_stacks", "gf_S4StatusStacks", ("str", "int")),
    ("transfer_status", "gf_S4StatusTransfer", ("unit1", "str")),
    ("reset_cooldowns", "gf_S4ClearCooldowns", ()),
    ("force_cooldown", "gf_S4UnitCooldownSet", ("str", "num")),
    ("clear_cooldown", "gf_S4UnitCooldownClear", ("str",)),
    ("spend_charges", "gf_S4UnitChargesSpend", ("str", "num")),
    ("restore_charges", "gf_S4UnitChargesRestore", ("str",)),
    ("force_ability_cooldown", "gf_S4AbilCooldownAdd", ("str", "str", "num")),
    ("clear_ability_cooldown", "gf_S4AbilCooldownClear", ("str", "str")),
    ("spend_ability_charges", "gf_S4AbilChargesSpend", ("str", "str", "num")),
    ("restore_ability_charges", "gf_S4AbilChargesRestore", ("str", "str")),
    ("reset_ability", "gf_S4AbilReset", ("str",)),
    ("force_status_cooldown", "gf_S4StatusCooldownAdd", ("str", "str", "num")),
    ("clear_status_cooldown", "gf_S4StatusCooldownClear", ("str", "str")),
    ("spend_status_charges", "gf_S4StatusChargesSpend", ("str", "str", "num")),
    ("restore_status_charges", "gf_S4StatusChargesRestore", ("str", "str")),
    ("force_vital", "gf_S4VitalSet", ("vital_prop", "num")),
    ("pause_progress", "gf_S4ProgressPause", ()),
    ("force_state", "gf_S4StateSet", ("state", "bool")),
]:
    lower_act(_name)(_apply(_helper, *_fmt))


@lower_act("force_enable")
def _(lo, c, p):
    need(lo, "gf_S4AbilityEnable")
    return [p + f"gf_S4AbilityEnable({lo._group(nm(c, 0))}, {gs(st(c, 1))}, true);"]


@lower_act("force_disable")
def _(lo, c, p):
    need(lo, "gf_S4AbilityEnable")
    return [p + f"gf_S4AbilityEnable({lo._group(nm(c, 0))}, {gs(st(c, 1))}, false);"]


def _regen(helper_full, helper_left, nstr):
    def lower(lo, c, p):
        mode = voc(c, 1 + nstr + 1, REGEN)
        helper = helper_full if mode == "full" else helper_left
        need(lo, helper)
        strs = ", ".join(gs(st(c, i)) for i in range(1, 1 + nstr))
        return [p + f"{helper}({lo._group(nm(c, 0))}, {strs}, {fx(numv(c, 1 + nstr))});"]
    return lower


lower_act("force_charge_regen")(_regen("gf_S4UnitChargeRegenFull", "gf_S4UnitChargeRegenLeft", 1))
lower_act("force_ability_charge_regen")(_regen("gf_S4AbilChargeRegenFull", "gf_S4AbilChargeRegenLeft", 2))
lower_act("force_status_charge_regen")(_regen("gf_S4StatusChargeRegenFull", "gf_S4StatusChargeRegenLeft", 2))


@lower_act("force_alliance")
def _(lo, c, p):
    return [p + f"libNtve_gf_SetAlliance({side(lo, c, 0)}, {side(lo, c, 1)}, {K(ALLIANCE[voc(c, 2, ALLIANCE)])});"]


@lower_act("force_upgrade")
def _(lo, c, p):
    return [p + f"TechTreeUpgradeAddLevel({side(lo, c, 0)}, {gs(st(c, 1))}, {ix(numv(c, 2))});"]


# existing builtin actions that gain an enemy-side lowering in v0.4
def lower_control(lo, c, p):
    """control(F, X): X changes owner to F's player (rewrite)."""
    need(lo, "gf_S4ForceOwner")
    return [p + f"gf_S4ForceOwner({lo._group(nm(c, 1))}, {lo.ext_owner(nm(c, 0))});"]


def lower_build(lo, c, p):
    """build(F, Asset, R) for an enemy F: spawn a construction-stage Asset at a valid placement in R."""
    need(lo, "gf_S4Build")
    asset = nm(c, 1)
    b = lo.bound[asset]
    utype = b.dynamic_unit_type or (b.spawn_components[0].unit_type if b.spawn_components else None)
    if not utype:
        err(f"build: asset '{asset}' needs a unit_type in its binding")
    sink = b.global_name if b.dynamic_owner is None else "UnitGroupEmpty()"
    cc, r = lo._region_geom(nm(c, 2))
    return [p + f"gf_S4Build({sink}, {gs(utype)}, {lo.ext_owner(asset)}, {cc}, {r});"]


# ------------------------------------------------------------------ per-strategy state
class ExtensionState:
    """Names claimed lazily so unused features emit nothing."""

    def __init__(self, lo):
        self.lo = lo
        self.slots: dict[str, int] = {}
        self.rejected: dict[str, str] = {}
        self.revealers: dict[tuple, str] = {}
        self.side_groups: dict[str, str] = {}
        self.side_players: dict[str, list[int]] = {}
        self.uses_memory = False
        # Hex encoding is injective even for Unicode and delimiter-containing
        # source keys. The kind separates user values from snapshot metadata.
        self.memory_namespace = "strat_" + lo.s.name.encode("utf-8").hex()
        self.memory_keys: dict[str, None] = {}
        self.attached: list[tuple[str, str]] = []  # (region global, force name)

    def memory_key(self, name: str, kind: str = "user") -> str:
        value = f"{self.memory_namespace}:{kind}:{name.encode('utf-8').hex()}"
        self.memory_keys[value] = None
        self.uses_memory = True
        return value

    def slot(self, name: str) -> str:
        if name not in self.slots:
            if len(self.slots) >= 64:
                err("more than 64 tag slots")
            self.slots[name] = len(self.slots)
        return str(self.slots[name])

    def rejected_flag(self, force: str) -> str:
        if force not in self.rejected:
            self.rejected[force] = self.lo._unique_global_name(f"gv_order_rejected_{force}")
        return self.rejected[force]

    def revealer_for(self, phase: Optional[str], call) -> str:
        if phase is None:
            err("reveal_while(...) is only allowed in a phase do-block")
        k = (phase, id(call))
        if k not in self.revealers:
            self.revealers[k] = self.lo._unique_global_name(f"gv_revealer_{phase}_{len(self.revealers) + 1}")
        return self.revealers[k]


def discover(lo):
    """Pre-claim names for features used anywhere in the strategy (deterministic order)."""
    s = lo.s
    st_ = lo.ext_state
    exprs = [d.expr for d in s.derived] + [t.guard for t in s.plan.transitions]
    calls = [c for e in exprs for c in walk_calls(e)]
    for n in [*s.plan.nodes, *s.plan.transitions]:
        block = getattr(n, "actions", None)
        if block:
            for a in block.actions:
                calls.append(a)
                for arg in a.args:
                    calls.extend(walk_calls(arg))
    for n in s.plan.nodes:  # reveal_while revealers belong to their phase
        block = getattr(n, "actions", None)
        if block and hasattr(n, "purpose"):
            for a in block.actions:
                if a.name == "reveal_while":
                    st_.revealer_for(n.id, a)
    for c in calls:
        if c.name in MEMORY:
            st_.uses_memory = True
            idx = MEMORY_KEY_INDEX.get(c.name, 0)
            if len(c.args) > idx and isinstance(c.args[idx], StringExpr):
                name = c.args[idx].value
                st_.memory_key(name)
                if c.name in {"snapshot", "snapshot_lost", "forget"}:
                    st_.memory_key(name, kind="snapshot_size")
        if c.name in ("tag", "count_tagged") and len(c.args) > 1 and isinstance(c.args[1], StringExpr):
            st_.slot(c.args[1].value)
        if c.name == "order_rejected" and c.args and isinstance(c.args[0], NameExpr):
            st_.rejected_flag(c.args[0].name)
    setup = next((b.value for b in s.bindings if b.name == "__setup__"), None)
    if isinstance(setup, BindingCall):
        for a in setup.args:
            if a.name == "sides":
                for item in (a.value if isinstance(a.value, list) else []):
                    if isinstance(item, BindingCall) and item.name == "side":
                        sname = _a(item, "name", 0)
                        players = [int(x) for x in (_a(item, "players", 1) or [])]
                        st_.side_players[sname] = players
                        st_.side_groups[sname] = lo._unique_global_name(f"gv_side_{sname}")


def _flag(v) -> str:
    if not isinstance(v, bool):
        err(f"expected true/false, got {v!r}")
    return "true" if v else "false"


def _player(lo, v) -> int:
    return lo.ext_player(v)


def global_lines(lo) -> tuple[list[str], list[str]]:
    st_ = lo.ext_state
    decl, init = [], []
    for gv in st_.side_groups.values():
        decl.append(f"playergroup {gv};")
        init.append(f"    {gv} = PlayerGroupEmpty();")
    for gv in st_.rejected.values():
        decl.append(f"bool {gv};")
        init.append(f"    {gv} = false;")
    for gv in st_.revealers.values():
        decl.append(f"revealer {gv};")
    return decl, init


def spawn_lines(lo) -> list[str]:
    st_ = lo.ext_state
    out = []
    # Never clear the engine's entire global data table: other map scripts
    # may own unrelated entries. All DSL keys are literals, so the compiler
    # can enumerate exactly the values this strategy owns.
    for memory_key in st_.memory_keys:
        out.append(f"    DataTableValueRemove(true, {gs(memory_key)});")
    for sname, gv in st_.side_groups.items():
        out.append(f"    {gv} = PlayerGroupEmpty();")
        out += [f"    PlayerGroupAdd({gv}, {p});" for p in st_.side_players[sname]]
    for gv in st_.rejected.values():
        out.append(f"    {gv} = false;")
    for gv, force in st_.attached:
        need(lo, "gf_S4AttachRegion")
        out.append(f"    gf_S4AttachRegion({gv}, {lo._group(force)});")
    return out


def poll_prefix_lines(lo) -> list[str]:
    return [f"    gf_S4AttachRegion({gv}, {lo._group(force)});" for gv, force in lo.ext_state.attached]


def setup_lines(lo, setup) -> list[str]:
    """v0.4 setup(...) options (rewrites of the initial world). Item syntax
    follows LOWERING_SPEC_v04: positional arguments, named ones optional."""
    out: list[str] = []
    if not isinstance(setup, BindingCall):
        return out

    def group(name):
        return lo._group(str(name))

    def item_calls(a, *names):
        items = a.value if isinstance(a.value, list) else [a.value]
        for it in items:
            if isinstance(it, BindingCall) and it.name in V03_SETUP_ITEMS:
                continue  # v0.3 items are dispatched by name, whatever the key
            if not isinstance(it, BindingCall) or (names and it.name not in names):
                err(f"setup {a.name}=[...] expects {' / '.join(names)}(...) items, got {it!r}")
            yield it

    for a in setup.args:
        if a.name == "alliance":
            for it in item_calls(a, "relation"):
                setting = _a(it, "setting", 2)
                if setting not in ("ally", "enemy", "neutral"):
                    err('relation(a, b, "ally"|"enemy"|"neutral", vision=bool)')
                v = _a(it, "vision", 3, False)
                key_ = setting + ("_vision" if v is True else "")
                if _a(it, "control", 4, False) is True:
                    if setting != "ally":
                        err("relation(..., control=true) needs \"ally\"")
                    key_ = "ally_vision_control"
                out.append(f"    libNtve_gf_SetAlliance({_player(lo, _a(it, 'a', 0))}, {_player(lo, _a(it, 'b', 1))}, {K(ALLIANCE[key_])});")
        elif a.name == "tech":
            for it in item_calls(a, "restrict", "allow", "requirement"):
                pl = _player(lo, _a(it, "player", 0))
                if it.name == "restrict":
                    out.append(f"    TechTreeRestrictionsEnable({pl}, {_flag(_a(it, 'enabled', 1, True))});")
                elif it.name == "allow":
                    kind, name, ok = _a(it, "kind", 1), gs(str(_a(it, "name", 2))), _flag(_a(it, "allowed", 3, True))
                    if kind == "ability":
                        out.append(f"    TechTreeAbilityAllow({pl}, AbilityCommand({name}, 0), {ok});")
                    elif kind in ("unit", "upgrade", "behavior"):
                        out.append(f"    TechTree{kind.capitalize()}Allow({pl}, {name}, {ok});")
                    else:
                        err("tech allow kind must be unit/upgrade/behavior/ability")
                else:
                    out.append(f"    TechTreeSpecificRequirementEnable({pl}, {gs(str(_a(it, 'name', 1)))}, {_flag(_a(it, 'enabled', 2, True))});")
        elif a.name == "ability":
            for it in item_calls(a, "ability"):
                need(lo, "gf_S4AbilityEnable")
                g, name = group(_a(it, "target", 0)), gs(str(_a(it, "name", 1)))
                out.append(f"    gf_S4AbilityEnable({g}, {name}, {_flag(_a(it, 'enabled', 2, True))});")
                level = _a(it, "level", 3)
                if level is not None:
                    need(lo, "gf_S4AbilityLevel")
                    out.append(f"    gf_S4AbilityLevel({g}, {name}, {ix(level)});")
        elif a.name == "share_vision":
            for it in item_calls(a, "share"):
                need(lo, "gf_S4ShareVision")
                out.append(f"    gf_S4ShareVision({group(_a(it, 'target', 0))}, {_player(lo, _a(it, 'side', 1))});")
        elif a.name == "cargo":
            for it in item_calls(a, "load"):
                t = group(_a(it, "transport", 0))
                out.append(f"    UnitCargoCreate(UnitGroupUnit({t}, 1), {gs(str(_a(it, 'unit_type', 1)))}, {ix(_a(it, 'count', 2, 1))});")
                into = _a(it, "into", 3)
                if into:
                    out.append(f"    UnitGroupAddUnitGroup({lo.ext_static_group(str(into))}, UnitCargoLastCreatedGroup());")
        elif a.name == "progress":
            for it in item_calls(a, "progress"):
                need(lo, "gf_S4ProgressSet")
                pct = _a(it, "percent", 1)
                if not isinstance(pct, (int, float)) or isinstance(pct, bool) or not 0 <= pct <= 100:
                    err("progress(X, percent) needs 0..100")
                out.append(f"    gf_S4ProgressSet({group(_a(it, 'target', 0))}, {ix(pct)});")
        elif a.name == "damage":
            for it in item_calls(a, "damage_scale"):
                need(lo, "gf_S4DamageScale")
                d, o = _a(it, "mode", 1), _a(it, "option", 2)
                if d not in DAMAGE_DIR or o not in DAMAGE_OPT:
                    err("damage_scale(X, deal|take, full|no|minimal|mega|mega2)")
                out.append(f"    gf_S4DamageScale({group(_a(it, 'target', 0))}, {K(DAMAGE_DIR[d])}, {K(DAMAGE_OPT[o])});")
        elif a.name in ("invulnerable", "uncommandable", "asleep"):
            helper = {"invulnerable": "gf_S4SetInvulnerable", "uncommandable": "gf_S4Uncommandable", "asleep": "gf_S4ForceSleep"}[a.name]
            for it in (a.value if isinstance(a.value, list) else [a.value]):
                need(lo, helper)
                out.append(f"    {helper}({group(it)}, true);")
        elif a.name == "weapons":
            for it in item_calls(a, "weapon"):
                g = group(_a(it, "target", 0))
                if _named(it, "add"):
                    need(lo, "gf_S4WeaponAdd")
                    out.append(f"    gf_S4WeaponAdd({g}, {gs(str(_named(it, 'add')))}, {gs(str(_named(it, 'turret', '')))});")
                if _named(it, "remove"):
                    need(lo, "gf_S4WeaponRemove")
                    out.append(f"    gf_S4WeaponRemove({g}, {gs(str(_named(it, 'remove')))});")
        elif a.name == "explored":
            for it in item_calls(a, "explore"):
                out.append(f"    VisExploreArea({_player(lo, _a(it, 'side', 0))}, {lo._region(str(_a(it, 'region', 1)))}, true, false);")
        elif a.name == "fill":
            for it in item_calls(a, "fog_fill"):
                ft = _a(it, "type", 2, "fogged")
                if ft not in FILL_TYPES:
                    err(f"fog_fill type must be one of {sorted(FILL_TYPES)}")
                out.append(f"    VisFillArea({_player(lo, _a(it, 'side', 0))}, {lo._region(str(_a(it, 'region', 1)))}, {K(FILL_TYPES[ft])}, false);")
        elif a.name == "no_fly":
            for it in (a.value if isinstance(a.value, list) else [a.value]):
                cc, r = lo._region_geom(str(it))
                out.append(f"    PathAddNoFlyZone({cc}, {r}, ({r} * 1.5));")
        elif a.name == "playable":
            out.append(f"    RegionPlayableMapSet({lo._region(str(a.value))});")
    return out


# ------------------------------------------------------------------ order validation wrapper
def _split_top(s: str) -> list[str]:
    parts, depth, cur, q = [], 0, "", False
    for ch in s:
        if ch == '"':
            q = not q
        if not q:
            if ch == "(":
                depth += 1
            elif ch == ")":
                depth -= 1
            elif ch == "," and depth == 0:
                parts.append(cur.strip())
                cur = ""
                continue
        cur += ch
    parts.append(cur.strip())
    return parts


def guard_orders(lines: list[str], flag: str) -> list[str]:
    out = []
    for line in lines:
        body = line.strip()
        if body.startswith("UnitGroupIssueOrder(") and body.endswith(");"):
            g, order, _q = _split_top(body[len("UnitGroupIssueOrder("):-2])
            p = line[: len(line) - len(line.lstrip())]
            out += [p + f"if (UnitOrderIsValid(UnitGroupUnit({g}, 1), {order}) == false) {{",
                    p + f"    {flag} = true;", p + "}"]
        out.append(line)
    return out
