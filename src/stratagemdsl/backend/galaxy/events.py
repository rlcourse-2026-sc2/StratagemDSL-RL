"""Event registration lowering."""
from __future__ import annotations


from stratagemdsl.core.model import (
    NameExpr, StringExpr, CallExpr,
)
from stratagemdsl.backend.galaxy import extensions as ext
from stratagemdsl.backend.galaxy.errors import LoweringError


class EventLowering:
    """DSL `on` events -> TriggerAddEvent* registrations plus identity guards."""

    def _event_identity_guards(self, subject: str) -> list[str]:
        b = self.bound.get(subject)
        if b is None or b.decl.kind not in {"force", "asset"}:
            return []
        # Exact group membership is preferable to type-only filtering. Because the group
        # variables are assigned at spawn time, this also distinguishes same-type subgroups.
        return [f"UnitGroupHasUnit({self._group(subject)}, EventUnit()) == true"]

    def emit_event_registration(self, event: CallExpr, trigger_name: str) -> tuple[list[str], list[str]]:
        n = event.name
        if n in {"enter", "leave"}:
            if len(event.args) != 2 or not all(isinstance(a, NameExpr) for a in event.args):
                raise LoweringError(f"{n}(force, region) expected")
            subj, region = event.args[0].name, event.args[1].name
            reg = self.bound.get(region)
            if reg is None or reg.decl.kind != "region":
                raise LoweringError(f"event {n}: '{region}' is not a region")
            entering = "true" if n == "enter" else "false"
            lines = [f"    TriggerAddEventUnitRegion({trigger_name}, null, {reg.global_name}, {entering});"]
            return lines, self._event_identity_guards(subj)

        if n == "unit_died":
            if len(event.args) not in {1, 2} or not all(isinstance(a, NameExpr) for a in event.args):
                raise LoweringError("unit_died(victim [, killer_force]) expected")
            subj = event.args[0].name
            guards = self._event_identity_guards(subj)
            if len(event.args) == 2:
                killer = event.args[1].name
                guards.extend(["libNtve_gf_KillingUnit() != null", f"UnitGroupHasUnit({self._group(killer)}, libNtve_gf_KillingUnit()) == true"])
            return [f"    TriggerAddEventUnitDied({trigger_name}, null);"], guards

        if n == "unit_attacked":
            if len(event.args) not in {1, 2} or not all(isinstance(a, NameExpr) for a in event.args):
                raise LoweringError("unit_attacked(victim [, attacking_force]) expected")
            subj = event.args[0].name
            guards = self._event_identity_guards(subj)
            if len(event.args) == 2:
                attacker = event.args[1].name
                guards.extend(["EventUnitTarget() != null", f"UnitGroupHasUnit({self._group(attacker)}, EventUnitTarget()) == true"])
            return [f"    TriggerAddEventUnitAttacked2({trigger_name}, null, null);"], guards

        if n == "unit_became_idle":
            if len(event.args) != 1 or not isinstance(event.args[0], NameExpr):
                raise LoweringError("unit_became_idle(force) expected")
            return [f"    TriggerAddEventUnitBecomesIdle({trigger_name}, null, true);"], self._event_identity_guards(event.args[0].name)

        if n in {"ability_completed", "ability_cast"}:
            if len(event.args) != 2 or not isinstance(event.args[0], NameExpr) or not isinstance(event.args[1], StringExpr):
                raise LoweringError(f'{n}(entity, "Ability") expected')
            subj = event.args[0].name
            ability = event.args[1].value
            stage = "c_unitAbilStageComplete" if n == "ability_completed" else "c_abilEffectStageCast"
            lines = [
                f'    TriggerAddEventUnitAbility({trigger_name}, null, AbilityCommand("{ability}", 0), {stage}, false);'
            ]
            return lines, self._event_identity_guards(subj)

        if n == "construction_completed":
            if len(event.args) != 1 or not isinstance(event.args[0], NameExpr):
                raise LoweringError("construction_completed(asset) expected")
            subj = event.args[0].name
            lines = [
                f"    TriggerAddEventUnitConstructProgress({trigger_name}, null, c_unitProgressStageComplete);"
            ]
            return lines, self._event_identity_guards(subj)

        if n == "timer":
            return [f"    TriggerAddEventTimer({trigger_name}, {self.ext_timer(event)});"], []
        if n == "unit_damaged":
            subject = self._name_arg(event, 0)
            guards = self._event_identity_guards(subject)
            if len(event.args) == 2:
                guards.append(f"UnitGroupHasUnit({self._group(self._name_arg(event, 1))}, EventUnitDamageSourceUnit()) == true")
            return [f"    TriggerAddEventUnitDamaged({trigger_name}, null, c_unitDamageTypeAny, c_unitDamageEither, null);"], guards
        if n == "effect_used":
            subject = self._name_arg(event, 0)
            if len(event.args) != 2 or not isinstance(event.args[1], StringExpr):
                raise LoweringError('effect_used(force, "Effect") expected')
            return [f"    TriggerAddEventPlayerEffectUsed({trigger_name}, c_playerAny, {self.emit_expr(event.args[1])});"], [f"UnitGroupHasUnit({self._group(subject)}, EventPlayerEffectUsedUnitLaunch()) == true"]
        if n in ext.LOWER_EV:
            return ext.LOWER_EV[n](self, event, trigger_name)
        raise LoweringError(f"unsupported event '{n}'")

