"""Expression and transition-guard lowering."""
from __future__ import annotations

from typing import Optional

from stratagemdsl.core.model import (
    Expr, NameExpr, BoolExpr, NumberExpr, StringExpr,
    CallExpr, UnaryExpr, BinaryExpr,
)
from stratagemdsl.registry import extensions as api
from stratagemdsl.backend.galaxy import extensions as ext
from stratagemdsl.backend.galaxy.errors import LoweringError
from stratagemdsl.backend.galaxy.bindings import (
    DEFAULT_FILTER, _str_value,
)


class ExpressionLowering:
    """DSL expressions and transition guards -> Galaxy expressions."""

    def _world_type(self, name: str) -> Optional[str]:
        b = self.bound.get(name)
        return b.decl.kind if b else None

    def _side(self, name: str) -> str:
        b = self.bound.get(name)
        return b.side if b else ""

    def _group(self, name: str) -> str:
        b = self.bound.get(name)
        if b is None or b.decl.kind not in {"force", "asset"}:
            raise LoweringError(f"'{name}' is not a bound force/asset")
        if b.dynamic_owner is not None:
            unit_type = f'UnitTypeFromString("{b.dynamic_unit_type}")' if b.dynamic_unit_type else 'null'
            unit_filter = DEFAULT_FILTER
            if b.hallucinated:
                # Hallucination is bit 37 in the historical NativeLib symbol cache;
                # the second UnitFilter argument contains required high bits.
                unit_filter = DEFAULT_FILTER.replace("UnitFilter(0, 0,", "UnitFilter(0, (1 << (c_targetFilterHallucination - 32)),")
            return (
                f"UnitGroup({unit_type}, {b.dynamic_owner}, RegionEntireMap(), "
                f"{unit_filter}, 0)"
            )
        return b.global_name

    def _region(self, name: str) -> str:
        b = self.bound.get(name)
        if b is None or b.decl.kind != "region":
            raise LoweringError(f"'{name}' is not a bound region")
        return b.global_name

    def _point_of_location(self, name: str) -> str:
        b = self.bound.get(name)
        if b is None:
            raise LoweringError(f"unknown location '{name}'")
        if b.decl.kind == "region" and b.region_center is not None:
            return b.region_center.emit()
        if b.decl.kind == "region":
            return self._region_geom(name)[0]
        if b.decl.kind in {"force", "asset"} and b.spawn_components:
            return b.spawn_components[0].point.emit()
        raise LoweringError(f"location '{name}' has no point lowering yet")

    def _group_count(self, name: str) -> str:
        return f"UnitGroupCount({self._group(name)}, c_unitCountAlive)"

    def emit_expr(self, e: Expr, _stack: Optional[set[str]] = None) -> str:
        stack = set() if _stack is None else set(_stack)
        if isinstance(e, BoolExpr):
            return "true" if e.value else "false"
        if isinstance(e, NumberExpr):
            return _str_value(e.value)
        if isinstance(e, StringExpr):
            escaped = e.value.replace('\\', '\\\\').replace('"', '\\"')
            return f'"{escaped}"'
        if isinstance(e, NameExpr):
            if e.name in self.derived:
                if e.name in stack:
                    raise LoweringError(f"recursive derived fact '{e.name}'")
                stack.add(e.name)
                return f"({self.emit_expr(self.derived[e.name], stack)})"
            if e.name in self.bound:
                kind = self.bound[e.name].decl.kind
                if kind in {"force", "asset"}:
                    return self._group(e.name)
                if kind == "region":
                    return self._region(e.name)
            raise LoweringError(f"cannot lower bare name '{e.name}' to Galaxy")
        if isinstance(e, UnaryExpr):
            if e.op == "not":
                return f"!({self.emit_expr(e.operand, stack)})"
            if e.op == "-":
                return f"-({self.emit_expr(e.operand, stack)})"
            raise LoweringError(f"unsupported unary op {e.op}")
        if isinstance(e, BinaryExpr):
            op = {"and": "&&", "or": "||", "implies": "||"}.get(e.op, e.op)
            if e.op == "implies":
                # A -> B === !A || B
                return f"(!({self.emit_expr(e.left, stack)}) || ({self.emit_expr(e.right, stack)}))"
            return f"({self.emit_expr(e.left, stack)} {op} {self.emit_expr(e.right, stack)})"
        if isinstance(e, CallExpr):
            args = e.args
            n = e.name
            if n in ext.LOWER_FN:
                return ext.LOWER_FN[n](self, e)
            v03 = self._emit_interaction_call(e)
            if v03 is not None:
                return v03
            if n == "alive" and len(args) == 1 and isinstance(args[0], NameExpr):
                return f"({self._group_count(args[0].name)} > 0)"
            if n in {"destroyed", "defeated"} and len(args) == 1 and isinstance(args[0], NameExpr):
                return f"({self._group_count(args[0].name)} == 0)"
            if n == "count" and len(args) == 1 and isinstance(args[0], NameExpr):
                return self._group_count(args[0].name)
            if n == "count_in" and len(args) == 2 and all(isinstance(a, NameExpr) for a in args):
                g, r = args[0].name, args[1].name
                return f"UnitGroupCount(UnitGroupFilterRegion({self._group(g)}, {self._region(r)}, 0), c_unitCountAlive)"
            if n in {"apparent_count", "player_unit_count"} and len(args) == 1 and isinstance(args[0], NameExpr):
                force = args[0].name
                b = self.bound.get(force)
                if b is None or b.decl.kind != "force" or b.owner is None:
                    raise LoweringError(f"{n} expects a force with numeric binding owner")
                return f"UnitGroupCount(UnitGroup(null, {b.owner}, RegionEntireMap(), {DEFAULT_FILTER}, 0), c_unitCountAlive)"
            if n == "distance" and len(args) == 2 and all(isinstance(a, NameExpr) for a in args):
                a, b = args[0].name, args[1].name
                return (
                    f"DistanceBetweenPoints(UnitGroupCenterOfGroup({self._group(a)}), "
                    f"UnitGroupCenterOfGroup({self._group(b)}))"
                )
            if n == "mission_time" and not args:
                return "GameGetMissionTime()"
            if n == "after" and len(args) == 1:
                return f"(GameGetMissionTime() >= {self.emit_expr(args[0], stack)})"
            if n == "construction_complete" and len(args) == 1 and isinstance(args[0], NameExpr):
                b = self.bound.get(args[0].name)
                if (b is None or b.decl.kind != "asset" or b.dynamic_owner is not None
                        or len(b.spawn_components) != 1 or b.spawn_components[0].count != 1):
                    raise LoweringError("construction_complete requires one stable, bound Asset unit")
                group = self._group(args[0].name)
                return f"(UnitGroupCount({group}, c_unitCountAlive) > 0 && !libNtve_gf_UnitIsUnderConstruction(UnitGroupUnit({group}, 1)))"
            if n == "in_region" and len(args) == 2 and all(isinstance(a, NameExpr) for a in args):
                # v0.1 means: at least one member of the group is in the region.
                g, r = args[0].name, args[1].name
                return f"(UnitGroupCount(UnitGroupFilterRegion({self._group(g)}, {self._region(r)}, 0), c_unitCountAlive) > 0)"
            if n == "retargeted" or n == "relieved":
                raise LoweringError(
                    f"strategic predicate '{n}' is not directly observable in Galaxy v0.1; "
                    "use an event/flag/counter grounding for backend-relevant guards"
                )
            if n == "killed_in" and len(args) == 2 and all(isinstance(a, NameExpr) for a in args):
                spec = self._counter_for(args[0].name, args[1].name)
                return spec.global_name
            if n in {"path_passable", "center_passable"} and len(args) == 1 and isinstance(args[0], NameExpr):
                b = self.bound[args[0].name]
                return f"PointPathingPassable({self._region_geom(args[0].name)[0]})"
            if n == "path_connected" and len(args) == 2 and all(isinstance(a, NameExpr) for a in args):
                left, right = (self._region_geom(a.name)[0] for a in args)
                return f"PointPathingIsConnected({left}, {right})"
            if n == "creep_available" and len(args) == 1 and isinstance(args[0], NameExpr):
                b = self.bound[args[0].name]
                return f"CreepIsPresent({self._region_geom(args[0].name)[0]})"
            if n in {"tokens", "active"} and len(args) == 1 and isinstance(args[0], NameExpr):
                place = args[0].name
                if place not in self.net.places:
                    raise LoweringError(f"{n}({place}): '{place}' is not a plan place")
                m = self.net_name("m", place)
                return m if n == "tokens" else f"({m} > 0)"
            raise LoweringError(f"unsupported backend expression '{n}(...)'")
        raise LoweringError(f"unsupported expression node {type(e).__name__}")

    def _name_args(self, e: CallExpr, count: int) -> list[str]:
        if len(e.args) != count or not all(isinstance(a, NameExpr) for a in e.args):
            raise LoweringError(f"{e.name}(...) expects {count} named entities")
        return [a.name for a in e.args]

    def _event_unit_expr(self, role: str) -> str:
        ev = self._event_ctx
        if ev is None:
            raise LoweringError(f"event {role} requires an event-driven transition")
        table = {
            ("source", "unit_died"): "libNtve_gf_KillingUnit()",
            ("source", "unit_attacked"): "EventUnitTarget()",
            ("source", "unit_damaged"): "EventUnitDamageSourceUnit()",
            ("source", "damage_absorbed"): "EventUnitDamageSourceUnit()",
            ("source", "effect_used"): "EventPlayerEffectUsedUnitLaunch()",
            ("target", "effect_used"): "EventPlayerEffectUsedUnitImpact()",
            ("position", "effect_used"): "EventPlayerEffectUsedUnitLaunch()",
            ("source", "unit_healed"): "EventUnitHealLaunchUnit()",
            ("target", "acquired_target"): "libNtve_gf_AcquiredTarget()",
        }
        if (role, ev.name) in table:
            return table[role, ev.name]
        if role == "position" and ev.name != "timer" and ev.name not in api.PLAYER_EVENTS:
            return "EventUnit()"
        raise LoweringError(f"event '{ev.name}' does not provide a {role} unit")

    def _emit_interaction_call(self, e: CallExpr) -> Optional[str]:
        """Bridge the v0.3 observation layer expected by the v0.4 extension."""
        n = e.name
        if n == "elapsed":
            phase, = self._name_args(e, 1)
            return f"(GameGetMissionTime() - {self.phase_clock_specs[phase]})"
        if n == "visible_to":
            if len(e.args) != 2 or not isinstance(e.args[0], StringExpr) or not isinstance(e.args[1], NameExpr):
                raise LoweringError('visible_to("ally"|"enemy", entity) expected')
            target = e.args[1].name
            player = self.ext_player(e.args[0].value)
            if self._world_type(target) == "region":
                return f"VisIsVisibleForPlayer({player}, {self._region_geom(target)[0]})"
            self._helpers_used.add("gf_StratAnyVisible")
            return f"gf_StratAnyVisible({self._group(target)}, {player})"
        helpers = {"has_status": "gf_StratAnyHasBehavior", "life_ratio": "gf_StratLifeRatio", "nearest_distance": "gf_StratNearestDistance"}
        if n in helpers:
            h = helpers[n]
            self._helpers_used.add(h)
            return f"{h}({', '.join(self.emit_expr(a) for a in e.args)})"
        if n == "count_matching":
            if len(e.args) != 2 or not isinstance(e.args[1], StringExpr):
                raise LoweringError('count_matching(force, "filter") expected')
            required, excluded, errors = api.filter_masks(e.args[1].value)
            if errors:
                raise LoweringError("; ".join(errors))
            return f"UnitGroupCount(UnitGroupFilter(null, c_playerAny, {self._group(self._name_arg(e, 0))}, {ext.unit_filter_literal(required, excluded)}, 0), c_unitCountAlive)"
        if n == "targeting":
            force, target = self._name_args(e, 2)
            self._helpers_used.add("gf_StratTargeting")
            if self._world_type(target) == "region":
                center, radius = self._region_geom(target)
                return f"gf_StratTargeting({self._group(force)}, UnitGroupEmpty(), {center}, {radius})"
            return f"gf_StratTargeting({self._group(force)}, {self._group(target)}, UnitGroupCenterOfGroup({self._group(target)}), 6.0)"
        if n in {"event_source_in", "event_target_in"}:
            target, = self._name_args(e, 1)
            role = "source" if n == "event_source_in" else "target"
            unit = self._event_unit_expr(role)
            return f"({unit} != null && UnitGroupHasUnit({self._group(target)}, {unit}) == true)"
        if n == "event_amount":
            if e.args:
                raise LoweringError("event_amount() takes no arguments")
            if self._event_ctx is not None and self._event_ctx.name == "unit_damaged":
                return "EventUnitDamageAmount()"
            value = ext.emit_event_amount(self)
            if value is None:
                raise LoweringError("event_amount() requires a matching amount event")
            return value
        if n == "event_in":
            region, = self._name_args(e, 1)
            return f"RegionContainsPoint({self._region(region)}, UnitGetPosition({self._event_unit_expr('position')}))"
        return None

    def _expand_derived_expr(self, e: Expr, stack: Optional[set[str]] = None) -> Expr:
        stack = set() if stack is None else set(stack)
        if isinstance(e, NameExpr) and e.name in self.derived:
            if e.name in stack:
                raise LoweringError(f"recursive derived fact '{e.name}'")
            stack.add(e.name)
            return self._expand_derived_expr(self.derived[e.name], stack)
        return e

    _CMP_OPS = {"==", "!=", "<", "<=", ">", ">="}

    def _is_killed_in_call(self, e: Expr, current_dead_force: Optional[str]) -> bool:
        return (
            isinstance(e, CallExpr)
            and e.name == "killed_in"
            and len(e.args) == 2
            and all(isinstance(a, NameExpr) for a in e.args)
            and current_dead_force == e.args[0].name
        )

    def emit_transition_guard(self, guard: Expr, event: Optional[CallExpr]) -> tuple[str, list[str]]:
        """Lower a transition guard with event-aware counter semantics.

        During ``unit_died(F)``, a ``killed_in(F, R)`` occurrence must include the
        current death even if the bookkeeping trigger runs after the transition
        trigger. Every occurrence of killed_in(F, R) anywhere in the guard --
        not just when it happens to be directly one side of a top-level
        comparison -- gets replaced through the SAME mechanism: `numeric_pair`
        below tracks "the value this sub-expression takes if the just-died
        unit was inside R" and "...if it wasn't" as it walks up through any
        enclosing arithmetic, and only the comparison(s) that actually
        consume that value resolve it into a single boolean, gated on the
        region check, entirely local to that comparison (never hoisted as a
        standalone required precondition on the rest of the guard, which
        would silently turn an `or` containing killed_in(...) into an `and`
        -- that would silently turn an `or` containing killed_in into an `and`).

        The treatment is the same for every AST shape (bare comparison,
        `+ 0`, killed_in compared with killed_in, ...), so equivalent
        expressions always lower to equivalent guards.

        No `extra` guards are returned for killed_in specifically; the (now
        empty, kept for signature compatibility) second element lets future
        event-conditioned rewrites still add real prerequisites if needed.
        """
        extra: list[str] = []
        current_dead_force: Optional[str] = None
        if (
            event is not None
            and event.name == "unit_died"
            and len(event.args) in {1, 2}
            and isinstance(event.args[0], NameExpr)
        ):
            current_dead_force = event.args[0].name

        _ARITH_OPS = {"+", "-", "*", "/"}

        def numeric_pair(e: Expr) -> Optional[tuple[str, str, str]]:
            """(text_if_in_region, text_if_not_in_region, region_guard_text)
            if `e`'s value depends on whether this death was inside some
            region R (i.e. it contains killed_in(current_dead_force, R)
            somewhere), else None. Raises if two DIFFERENT regions' checks
            would need combining -- not supported, rejected loudly rather
            than silently using only one of them."""
            if self._is_killed_in_call(e, current_dead_force):
                force, region = e.args[0].name, e.args[1].name
                spec = self._counter_for(force, region)
                rg = self._event_position_in_region_guard(region)
                if spec.seen_global:
                    rg = f"({rg} && (UnitGroupHasUnit({spec.seen_global}, EventUnit()) == false))"
                return (f"({spec.global_name} + 1)", spec.global_name, rg)
            if isinstance(e, BinaryExpr) and e.op in _ARITH_OPS:
                lp, rp = numeric_pair(e.left), numeric_pair(e.right)
                if lp is None and rp is None:
                    return None
                if lp is not None and rp is not None and lp[2] != rp[2]:
                    raise LoweringError(
                        "killed_in(...) checks against more than one region combined in the "
                        "same arithmetic/comparison expression are not supported"
                    )
                rg = (lp or rp)[2]
                l_true, l_false = (lp[0], lp[1]) if lp else (self.emit_expr(e.left),) * 2
                r_true, r_false = (rp[0], rp[1]) if rp else (self.emit_expr(e.right),) * 2
                return (f"({l_true} {e.op} {r_true})", f"({l_false} {e.op} {r_false})", rg)
            if isinstance(e, UnaryExpr) and e.op == "-":
                # Negation keeps both event-adjusted branches, so every
                # occurrence of the counter in one expression sees the same
                # (post-death) value.
                inner = numeric_pair(e.operand)
                if inner is None:
                    return None
                return (f"(-({inner[0]}))", f"(-({inner[1]}))", inner[2])
            if isinstance(e, NameExpr) and e.name in self.derived:
                # A derived fact could itself be defined in terms of
                # killed_in(...) (e.g. `derive x = killed_in(f, r);`) --
                # propagate through it rather than silently treating the
                # reference as event-independent.
                return numeric_pair(self.derived[e.name])
            return None

        def emit_ev(e: Expr, stack: Optional[set[str]] = None) -> str:
            stack = set() if stack is None else set(stack)
            if isinstance(e, NameExpr) and e.name in self.derived:
                if e.name in stack:
                    raise LoweringError(f"recursive derived fact '{e.name}'")
                stack.add(e.name)
                return f"({emit_ev(self.derived[e.name], stack)})"
            if isinstance(e, UnaryExpr):
                if e.op == "not":
                    return f"!({emit_ev(e.operand, stack)})"
                if e.op == "-":
                    return f"-({emit_ev(e.operand, stack)})"
            if isinstance(e, BinaryExpr):
                if e.op in self._CMP_OPS:
                    lp, rp = numeric_pair(e.left), numeric_pair(e.right)
                    if lp is not None or rp is not None:
                        if lp is not None and rp is not None and lp[2] != rp[2]:
                            raise LoweringError(
                                "killed_in(...) checks against more than one region combined "
                                "in the same comparison are not supported"
                            )
                        rg = (lp or rp)[2]
                        l_true, l_false = (lp[0], lp[1]) if lp else (emit_ev(e.left, stack),) * 2
                        r_true, r_false = (rp[0], rp[1]) if rp else (emit_ev(e.right, stack),) * 2
                        true_branch = f"({l_true} {e.op} {r_true})"
                        false_branch = f"({l_false} {e.op} {r_false})"
                        # "this death counts toward the comparison iff it happened
                        # inside R" -- entirely local to this one comparison, never
                        # a precondition on the rest of the guard.
                        return f"(({rg} && {true_branch}) || (!({rg}) && {false_branch}))"
                if e.op == "implies":
                    return f"(!({emit_ev(e.left, stack)}) || ({emit_ev(e.right, stack)}))"
                op = {"and": "&&", "or": "||"}.get(e.op, e.op)
                return f"({emit_ev(e.left, stack)} {op} {emit_ev(e.right, stack)})"
            if self._is_killed_in_call(e, current_dead_force):
                # A bare killed_in(...) with no enclosing comparison at all --
                # there is no ternary or bool->int coercion in Galaxy to
                # express "count only if in region" as a single number here,
                # so this shape is rejected explicitly rather than silently
                # guessing.
                raise LoweringError(
                    "killed_in(...) must be used inside a comparison (e.g. killed_in(f, r) >= 3); "
                    "using its bare value elsewhere is not supported"
                )
            return self.emit_expr(e, stack)

        previous, self._event_ctx = self._event_ctx, event
        try:
            return emit_ev(guard), extra
        finally:
            self._event_ctx = previous

