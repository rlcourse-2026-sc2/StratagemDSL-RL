"""Action lowering."""
from __future__ import annotations

from typing import Optional

from stratagemdsl.core.model import (
    NameExpr, StringExpr, CallExpr, ActionBlock,
)
from stratagemdsl.registry import extensions as api
from stratagemdsl.backend.galaxy import extensions as ext
from stratagemdsl.backend.galaxy.errors import LoweringError


class ActionLowering:
    """DSL actions -> Galaxy statements (enemy orders, env and rewrite actions)."""

    def _action_actor(self, call: CallExpr) -> Optional[str]:
        if not call.args or not isinstance(call.args[0], NameExpr):
            return None
        return call.args[0].name

    def _is_environment_action(self, call: CallExpr) -> bool:
        if call.name in api.ALWAYS_EMIT:
            return True  # v0.4 script/environment actions and rewrites
        actor = self._action_actor(call)
        if actor is None:
            return call.name in {"spawn"}
        side = self._side(actor).lower()
        if self.oracle and side == "ally":
            return True
        return side == "enemy"

    def _name_arg(self, call: CallExpr, idx: int) -> str:
        try:
            x = call.args[idx]
        except IndexError:
            raise LoweringError(f"action '{call.name}' misses argument {idx+1}")
        if not isinstance(x, NameExpr):
            raise LoweringError(f"action '{call.name}' argument {idx+1} must be a name")
        return x.name

    def emit_action(self, call: CallExpr, indent: int = 1) -> list[str]:
        lines = self._emit_action_lines(call, indent)
        actor = self._action_actor(call)
        if actor in self.ext_state.rejected and call.name in api.ORDER_ACTIONS:
            lines = ext.guard_orders(lines, self.ext_state.rejected[actor])
        return lines

    def _emit_action_lines(self, call: CallExpr, indent: int = 1) -> list[str]:
        p = "    " * indent
        n = call.name
        if n in api.ACTS and api.ACTS[n][1] in ("env", "rewrite"):
            return ext.LOWER_ACT[n](self, call, p)
        if not self._is_environment_action(call):
            self.notes.append(f"agent-side action not emitted: {n}")
            return [p + f"// agent-controlled: {n}(...)"]

        actor = self._name_arg(call, 0) if call.args else ""
        if n == "attack":
            target = self._name_arg(call, 1)
            return [
                p + f'UnitGroupIssueOrder({self._group(actor)}, '
                    f'OrderTargetingUnitGroup(AbilityCommand("attack", 0), {self._group(target)}), '
                    'c_orderQueueReplace);'
            ]
        if n == "retarget":
            target = self._name_arg(call, 1)
            # Retargeting an enemy force toward an enemy-owned asset means redeploy/defend,
            # not attack its own structure. Retargeting toward an opposing force is an attack.
            if self._world_type(target) == "region" or self._side(actor).lower() == self._side(target).lower():
                return [
                    p + f'UnitGroupIssueOrder({self._group(actor)}, '
                        f'OrderTargetingPoint(AbilityCommand("move", 0), {self._point_of_location(target)}), '
                        'c_orderQueueReplace);'
                ]
            return [
                p + f'UnitGroupIssueOrder({self._group(actor)}, '
                    f'OrderTargetingUnitGroup(AbilityCommand("attack", 0), {self._group(target)}), '
                    'c_orderQueueReplace);'
            ]
        if n in {"move", "retreat"}:
            target = self._name_arg(call, 1)
            ability = "move"
            order_constructor = "OrderTargetingRelativePoint" if n == "retreat" else "OrderTargetingPoint"
            return [
                p + f'UnitGroupIssueOrder({self._group(actor)}, '
                    f'{order_constructor}(AbilityCommand("{ability}", 0), {self._point_of_location(target)}), '
                    'c_orderQueueReplace);'
            ]
        if n == "hold":
            return [
                p + f'UnitGroupIssueOrder({self._group(actor)}, '
                    'Order(AbilityCommand("stop", 0)), c_orderQueueReplace);'
            ]
        if n == "set_mode":
            if len(call.args) != 2 or not isinstance(call.args[1], StringExpr):
                raise LoweringError("set_mode(entity, \"mode\") expected")
            mode = call.args[1].value.lower()
            ability = {
                "unsieged": "Unsiege",
                "sieged": "SiegeMode",
                "phasing": "PhasingMode",
            }.get(mode, call.args[1].value)
            return [
                p + f'UnitGroupIssueOrder({self._group(actor)}, '
                    f'Order(AbilityCommand("{ability}", 0)), c_orderQueueReplace);'
            ]
        if n == "cast":
            if len(call.args) < 2 or not isinstance(call.args[1], StringExpr):
                raise LoweringError("cast(force, \"Ability\" [, target]) expected")
            ability = call.args[1].value
            if len(call.args) == 2:
                return [p + f'UnitGroupIssueOrder({self._group(actor)}, Order(AbilityCommand("{ability}", 0)), c_orderQueueReplace);']
            target = call.args[2]
            if isinstance(target, NameExpr) and self._world_type(target.name) == "region":
                return [p + f'UnitGroupIssueOrder({self._group(actor)}, OrderTargetingPoint(AbilityCommand("{ability}", 0), {self._point_of_location(target.name)}), c_orderQueueReplace);']
            if isinstance(target, NameExpr) and self._world_type(target.name) in {"force", "asset"}:
                return [p + f'UnitGroupIssueOrder({self._group(actor)}, OrderTargetingUnitGroup(AbilityCommand("{ability}", 0), {self._group(target.name)}), c_orderQueueReplace);']
            raise LoweringError("unsupported cast target")
        if n == "block":
            target = self._name_arg(call, 1)
            return [p + f'UnitGroupIssueOrder({self._group(actor)}, OrderTargetingPoint(AbilityCommand("ForceField", 0), {self._point_of_location(target)}), c_orderQueueReplace);']
        if n == "spawn":
            target = self._name_arg(call, 1)
            b = self.bound.get(actor)
            if b is None or not b.spawn_components:
                raise LoweringError(f"spawn force '{actor}' needs a concrete spawn specification")
            pt = self._point_of_location(target)
            out = []
            # Ensure delayed groups start empty and accumulate newly created units.
            for c in b.spawn_components:
                out.extend(c.spawn_lines(p, b.global_name, pt))
            return out
        if n == "apply_effect":
            target = self._name_arg(call, 2)
            if len(call.args) != 3 or not isinstance(call.args[1], StringExpr):
                raise LoweringError('apply_effect(force, "Effect", target) expected')
            effect = self.emit_expr(call.args[1])
            if self._world_type(target) == "region":
                self._helpers_used.add("gf_StratApplyEffectPoint")
                return [p + f"gf_StratApplyEffectPoint({self._group(actor)}, {effect}, {self._point_of_location(target)});"]
            self._helpers_used.add("gf_StratApplyEffectUnit")
            return [p + f"gf_StratApplyEffectUnit({self._group(actor)}, {effect}, {self._group(target)});"]
        if n == "control":
            return ext.lower_control(self, call, p)
        if n == "build":
            return ext.lower_build(self, call, p)
        if n in {"cancel", "transport"}:
            raise LoweringError(f"environment action '{n}' needs a dedicated SC2 lowering rule")
        raise LoweringError(f"unsupported action '{n}'")

    def _emit_action_block(self, block: Optional[ActionBlock], indent: int = 1) -> list[str]:
        if block is None:
            return []
        lines: list[str] = []
        ordered_actors: set[str] = set()
        for a in block.actions:
            emitted = self.emit_action(a, indent)
            actor = self._action_actor(a)
            if block.mode == "sequence" and actor in ordered_actors:
                emitted = [line.replace("c_orderQueueReplace", "c_orderQueueAddToEnd") for line in emitted]
            if actor is not None and any("UnitGroupIssueOrder(" in line for line in emitted):
                ordered_actors.add(actor)
            lines.extend(emitted)
        return lines

