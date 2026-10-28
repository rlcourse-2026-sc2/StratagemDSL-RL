"""Lowerer state: Galaxy name allocation, discovery passes, extension API."""
from __future__ import annotations

from typing import Any, Optional

from stratagemdsl.core.ast_utils import walk_calls
from stratagemdsl.core.model import (
    Strategy, BindingCall, Expr, NameExpr, BoolExpr,
    NumberExpr, StringExpr, CallExpr, UnaryExpr, BinaryExpr, Transition,
)
from stratagemdsl.registry import extensions as api
from stratagemdsl.backend.galaxy import extensions as ext
from stratagemdsl.backend.galaxy.errors import LoweringError
from stratagemdsl.backend.galaxy.bindings import (
    _safe, _num, BoundEntity, CounterSpec, BindingResolver,
)
from stratagemdsl.net import build_net, event_signature


class LoweringState:
    """Name allocation, discovery passes and the lowerer API used by extensions."""

    def __init__(self, strategy: Strategy, *, oracle: bool = False, guard_oracle: bool = False,
                 gameover: bool = False):
        self.s = strategy
        # When set, reaching a terminal phase ends the game with GameOver
        # (success: allied players win, failure: they lose), so one game is one
        # scored episode -- what an LLM-PySC2 run needs. Off by default: MARL
        # training maps keep running and respawn every round.
        self.gameover = gameover
        # When set, allied order actions are emitted as Galaxy orders too.
        # The default leaves them as agent intents and only scripts the enemy.
        self.oracle = oracle
        # Test-only: every world guard becomes a settable bool global
        # (gv_net_guard_<t>) so the generated token game can be executed
        # offline against the reference simulator (debug.galaxy_vm).
        self.guard_oracle = guard_oracle
        # v0.6: the plan is lowered from its Petri net, not from the AST graph.
        self.net = build_net(strategy)
        self._net_names: dict[tuple[str, str], str] = {}
        # One registry for every Galaxy global and trigger name this lowerer
        # hands out. DSL name categories are not disjoint in Galaxy: an entity
        # named "phase_entered_wait" and a phase named "wait" both want
        # "gv_phase_entered_wait". Must exist before anything claims a name.
        self._used_global_names: set[str] = set()

        self.r = BindingResolver(strategy)
        self.bound: dict[str, BoundEntity] = {
            e.name: self.r.bind_entity(e) for e in strategy.world
        }
        # Entities claim their names first (most likely to matter for
        # readability/debugging since they echo the DSL's own vocabulary);
        # anything else that collides gets disambiguated instead.
        for b in self.bound.values():
            b.global_name = self._unique_global_name(b.global_name)

        setup = next((b.value for b in strategy.bindings if b.name == "__setup__"), None)
        policy = self.r.named(setup, "terminal_policy", "legacy") if isinstance(setup, BindingCall) else "legacy"
        if policy not in {"legacy", "first_wins"}:
            raise LoweringError("terminal_policy must be legacy or first_wins")
        self.terminal_policy = policy
        self.outcome_global = self._unique_global_name("gv_plan_outcome") if policy == "first_wins" else None
        self.gameover_global = self._unique_global_name("gv_plan_game_ended") if gameover else None

        self.derived = {d.name: d.expr for d in strategy.derived}
        self.node_map = {n.id: n for n in strategy.plan.nodes}
        self.notes: list[str] = []
        if oracle:
            self.notes.append("oracle: allied order actions are emitted as Galaxy orders")
        if gameover:
            self.notes.append("gameover: a terminal phase ends the game (GameOver victory/defeat)")
        self.counter_specs: dict[tuple[str, str], CounterSpec] = {}
        # Per-transition lowering classification, keyed by transition id, e.g.
        # {"kind": "event"} | {"kind": "instant_fold"} | {"kind": "periodic_poll"}
        # | {"kind": "error", "message": "..."}. Populated incrementally as
        # transitions are processed, so it is still readable (partially
        # filled) even if .emit() later raises -- used by views/plangraph.py
        # for the "validate on the graph" visualization.
        self.transition_kinds: dict[str, dict] = {}
        self._helpers_used: set[str] = set()
        self._event_ctx: Optional[CallExpr] = None
        self.timer_specs: dict[tuple[str, float], str] = {}
        self.phase_clock_specs: dict[str, str] = {}
        self.ext_state = ext.ExtensionState(self)
        self._current_phase: Optional[str] = None
        for b in self.bound.values():
            if b.decl.kind == "region" and b.region_kind == "attached":
                self.ext_state.attached.append((b.global_name, b.attached_to))
        self._discover_timing()
        ext.discover(self)
        self._discover_counters()
        # The validator rejects duplicate starts (P006_DUP_START); the backend
        # may receive unvalidated input, and a duplicate would put two tokens
        # into a one-token phase.
        if len(self.s.plan.start) != len(set(self.s.plan.start)):
            dupes = sorted({x for x in self.s.plan.start if self.s.plan.start.count(x) > 1})
            raise LoweringError(f"plan.start contains duplicate entries: {dupes}")

    def _discover_timing(self) -> None:
        """Allocate phase clocks and timers before any eager cascade is lowered."""
        exprs = [d.expr for d in self.s.derived]
        exprs += [t.guard for t in self.s.plan.transitions if t.guard is not None]
        for node in [*self.s.plan.nodes, *self.s.plan.transitions]:
            block = getattr(node, "actions", None)
            if block:
                exprs.extend(block.actions)
        for expr in exprs:
            for call in walk_calls(expr):
                if call.name == "elapsed" and len(call.args) == 1 and isinstance(call.args[0], NameExpr):
                    phase = call.args[0].name
                    if phase not in self.node_map:
                        raise LoweringError(f"elapsed references unknown phase '{phase}'")
                    if phase not in self.phase_clock_specs:
                        self.phase_clock_specs[phase] = self._unique_global_name(f"gv_phase_t0_{_safe(phase)}")
        for t in self.s.plan.transitions:
            ev = t.event
            if ev is None or ev.name != "timer":
                continue
            if (len(ev.args) != 2 or not isinstance(ev.args[0], NameExpr)
                    or not isinstance(ev.args[1], NumberExpr) or ev.args[1].value <= 0):
                raise LoweringError("timer(phase, positive_seconds) expected")
            phase, seconds = ev.args[0].name, float(ev.args[1].value)
            if phase not in self.node_map:
                raise LoweringError(f"timer references unknown phase '{phase}'")
            key = (phase, seconds)
            if key not in self.timer_specs:
                suffix = _safe(_num(seconds))
                self.timer_specs[key] = self._unique_global_name(f"gv_timer_{_safe(phase)}_{suffix}")

    def _phase_entry_timing(self, phase: str, indent: int = 1) -> list[str]:
        p = "    " * indent
        out = []
        if phase in self.phase_clock_specs:
            out.append(f"{p}{self.phase_clock_specs[phase]} = GameGetMissionTime();")
        for (node, seconds), gv in self.timer_specs.items():
            if node == phase:
                out.append(f"{p}TimerStart({gv}, {seconds!r}, false, c_timeGame);")
        return out

    def _phase_exit_resources(self, phase: str, indent: int = 1) -> list[str]:
        p = "    " * indent
        out = [f"{p}libNtve_gf_StopTimer({gv});" for (node, _), gv in self.timer_specs.items() if node == phase]
        for (node, _), gv in self.ext_state.revealers.items():
            if node == phase:
                out += [f"{p}if ({gv} != null) {{", f"{p}    VisRevealerDestroy({gv});", f"{p}    {gv} = null;", f"{p}}}"]
        return out

    def _unique_global_name(self, base: str) -> str:
        """General collision registry for any plain Galaxy global (entity
        unitgroup/region, phase active/entered flag, join count/fired,
        killed_in counter, ...) -- see the note in __init__. Unlike
        `_unique_trigger_name`, a plain global has no _Func/_Init
        derivatives to reserve alongside it.
        """
        name = base
        n = 2
        while name in self._used_global_names:
            name = f"{base}_{n}"
            n += 1
        self._used_global_names.add(name)
        return name

    def _unique_trigger_name(self, base: str) -> str:
        """Every Galaxy trigger variable name handed out -- whether derived
        directly from a user transition id or auto-generated for a combined
        dispatcher -- goes through this SAME registry `_unique_global_name`
        also uses, so an auto-generated name (or an internal bookkeeping
        global) can never silently collide with a legally-chosen user
        transition id or user entity/phase/join name.

        Reserves `base`, `base_Func` and `base_Init` together: Galaxy does not
        separate variable and function names, so trigger `hit_Func` would
        otherwise collide with trigger `hit`'s derived function `gt_hit_Func`.

        Example: a transition named `poll_wait` and the auto-generated poll
        dispatcher of source `wait` both want `gt_poll_wait`.
        """
        name = base
        n = 2
        while (
            name in self._used_global_names
            or f"{name}_Func" in self._used_global_names
            or f"{name}_Init" in self._used_global_names
        ):
            name = f"{base}_{n}"
            n += 1
        self._used_global_names.add(name)
        self._used_global_names.add(f"{name}_Func")
        self._used_global_names.add(f"{name}_Init")
        return name

    def _event_signature(self, event: CallExpr) -> tuple:
        return event_signature(event)

    # ------------------------------------------------------ net name pool
    def net_name(self, kind: str, key: str) -> str:
        """Stable Galaxy name for a net object: kind in m (marking), seen,
        en / fire (functions), guard (oracle bool)."""
        k = (kind, key)
        if k not in self._net_names:
            prefix = {"m": "gv_net_m_", "seen": "gv_net_seen_", "guard": "gv_net_guard_",
                      "en": "gf_net_en_", "fire": "gf_net_fire_"}[kind]
            self._net_names[k] = self._unique_global_name(prefix + _safe(key))
        return self._net_names[k]

    def _walk_expr(self, e: Expr):
        yield e
        if isinstance(e, CallExpr):
            for a in e.args:
                yield from self._walk_expr(a)
        elif isinstance(e, UnaryExpr):
            yield from self._walk_expr(e.operand)
        elif isinstance(e, BinaryExpr):
            yield from self._walk_expr(e.left)
            yield from self._walk_expr(e.right)

    def _discover_counters(self) -> None:
        exprs: list[Expr] = [d.expr for d in self.s.derived]
        for t in self.s.plan.transitions:
            if t.guard is not None:
                exprs.append(t.guard)
        for e in exprs:
            for x in self._walk_expr(e):
                if not isinstance(x, CallExpr) or x.name != "killed_in":
                    continue
                if len(x.args) != 2 or not all(isinstance(a, NameExpr) for a in x.args):
                    raise LoweringError("killed_in(force, region) expects name arguments")
                force, region = x.args[0].name, x.args[1].name
                key = (force, region)
                if key not in self.counter_specs:
                    # Length-prefixed components: plain "{force}_{region}" is
                    # ambiguous (killed_in(a_b, c) vs killed_in(a, b_c)).
                    f_safe, r_safe = _safe(force), _safe(region)
                    suffix = f"{len(f_safe)}_{f_safe}_{len(r_safe)}_{r_safe}"
                    self.counter_specs[key] = CounterSpec(
                        force=force,
                        region=region,
                        global_name=self._unique_global_name(f"gv_killed_in_{suffix}"),
                        trigger_name=self._unique_trigger_name(f"gt_count_killed_in_{suffix}"),
                        seen_global=self._unique_global_name(f"gv_counted_units_{suffix}") if self.outcome_global else None,
                    )

    def _counter_for(self, force: str, region: str) -> CounterSpec:
        try:
            return self.counter_specs[(force, region)]
        except KeyError:
            raise LoweringError(f"internal: missing counter for killed_in({force}, {region})")

    def _event_position_in_region_guard(self, region: str) -> str:
        b = self.bound.get(region)
        if b is not None and b.decl.kind == "region" and b.region_kind != "circle":
            return f"RegionContainsPoint({b.global_name}, UnitGetPosition(EventUnit()))"
        if b is None or b.decl.kind != "region" or b.region_center is None or b.region_radius is None:
            raise LoweringError("killed_in currently requires a circle region")
        return (
            f"DistanceBetweenPoints(UnitGetPosition(EventUnit()), "
            f"{b.region_center.emit()}) <= {b.region_radius}"
        )

    # --------------------------- v0.4: lowerer API ---------------------------

    def ext_player(self, side: Any) -> int:
        if isinstance(side, (int, float)) and not isinstance(side, bool):
            return int(side)
        players = self.ext_state.side_players.get(side)
        if players:
            return int(players[0])
        if side not in api.SIDES:
            raise LoweringError(f"unknown side {side!r}; use \"ally\" or \"enemy\"")
        return api.SIDES[side]

    def ext_owner(self, name: str) -> int:
        b = self.bound.get(name)
        if b is None or b.decl.kind not in {"force", "asset"}:
            raise LoweringError(f"'{name}' is not a bound force/asset")
        owner = b.dynamic_owner if b.dynamic_owner is not None else b.owner
        if owner is None:
            raise LoweringError(f"'{name}' has no owner")
        return owner

    def ext_timer(self, call: CallExpr) -> str:
        args = call.args
        if len(args) != 2 or not isinstance(args[0], NameExpr) or not isinstance(args[1], NumberExpr):
            raise LoweringError(f"{call.name}(phase, seconds) expected")
        k = (args[0].name, float(args[1].value))
        if k not in self.timer_specs:
            raise LoweringError(f"{call.name}({args[0].name}, {_num(k[1])}) needs a transition 'on timer({args[0].name}, {_num(k[1])})'")
        return self.timer_specs[k]

    def ext_static_group(self, name: str) -> str:
        b = self.bound.get(name)
        if b is None or b.decl.kind not in {"force", "asset"}:
            raise LoweringError(f"'{name}' is not a bound force/asset")
        if b.dynamic_owner is not None:
            raise LoweringError(f"'{name}' is a dynamic query; roster operations need a unit_group/unit roster")
        return b.global_name

    def ext_static_type(self, e: Expr) -> str:
        """Coarse Int/Float typing to decide int->fixed conversion."""
        from stratagemdsl.registry.builtins import FUNCTIONS
        if isinstance(e, NumberExpr):
            return "Int" if float(e.value).is_integer() else "Float"
        if isinstance(e, NameExpr) and e.name in self.derived:
            return self.ext_static_type(self.derived[e.name])
        if isinstance(e, CallExpr):
            sigs = FUNCTIONS.get(e.name) or []
            return sigs[0].returns if sigs else "Float"
        if isinstance(e, UnaryExpr):
            return self.ext_static_type(e.operand)
        if isinstance(e, BinaryExpr):
            lt, rt = self.ext_static_type(e.left), self.ext_static_type(e.right)
            return "Int" if lt == rt == "Int" and e.op != "/" else "Float"
        return "Float"

    def _region_geom(self, name: str) -> tuple[str, str]:
        """(center point expr, radius expr) for any v0.4 region shape. Non-circle
        regions use RegionGetCenter and half their width."""
        b = self.bound.get(name)
        if b is None or b.decl.kind != "region":
            raise LoweringError(f"'{name}' is not a bound region")
        if b.region_kind == "circle":
            return b.region_center.emit(), repr(float(b.region_radius))
        center = f"RegionGetCenter({b.global_name})"
        if b.region_kind == "attached":
            return center, repr(float(b.region_radius))
        return center, f"(libNtve_gf_WidthOfRegion({b.global_name}) / 2.0)"

    def _region_init_lines(self, b: BoundEntity) -> list[str]:
        gv = b.global_name
        if b.region_kind == "circle":
            return [f"    {gv} = RegionCircle({b.region_center.emit()}, {b.region_radius});"]
        if b.region_kind == "attached":
            return [f"    {gv} = RegionCircle(Point(0.0, 0.0), {float(b.region_radius)!r});"]
        if b.region_kind == "rect":
            return [f"    {gv} = RegionRect({', '.join(repr(x) for x in b.region_rect)});"]
        if b.region_kind == "whole_map":
            return [f"    {gv} = RegionEntireMap();"]
        return [f"    {gv} = RegionEmpty();"]

    def _region_build_lines(self) -> list[str]:
        """Union parts are added once at MapInit (InitGlobals only allows
        assignments); the region object itself is created in InitGlobals so
        event registrations made in InitTriggers see the same object."""
        out: list[str] = []
        for b in self.bound.values():
            if b.decl.kind != "region" or b.region_kind != "union":
                continue
            gv = b.global_name
            for part in b.region_parts:
                if part[0] == "rect":
                    out.append(f"    RegionAddRect({gv}, true, {', '.join(repr(x) for x in part[1])});")
                else:
                    out.append(f"    RegionAddCircle({gv}, true, {part[1].emit()}, {float(part[2])!r});")
        return out

