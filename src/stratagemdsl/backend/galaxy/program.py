"""Program assembly: the plan net's token game in Galaxy.

The plan is compiled by `stratagemdsl.net.build_net` into a Petri net; this
module emits that net's step semantics (`stratagemdsl.net.semantics`) as
Galaxy, so the generated map plays exactly the token game the analysis
explored:

    int  gv_net_m_<place>        marking (one counter per net place)
    bool gv_net_seen_<place>     entered-this-round flag of `once` places
    int  gv_plan_outcome         first_wins latch (0 running, 1 success, 2 failure)
    bool gv_plan_game_ended      only with gameover=True: GameOver already called

    bool gf_net_en_<t>()         enabling rule: inputs, read/inhibitor arcs, capacities
    void gf_net_fire_<t>()       consume, run actions, produce (entry actions, timers,
                                 terminal latch)
    void gf_net_settle()         fire enabled immediate transitions by rank until stable
    void gf_net_reset()          initial marking (gf_Spawn, every round)

    gt_net_ev_*                  one trigger per distinct event: snapshot the enabled
                                 candidates whose guard holds, fire them by rank, settle
    gt_net_tick                  the periodic poll for live-guarded eventless transitions

Rank = (priority, declaration order), the same tie-break as the simulator.
"""
from __future__ import annotations

from typing import Optional

from stratagemdsl.core.model import BindingCall, Phase
from stratagemdsl.backend.galaxy import extensions as ext
from stratagemdsl.backend.galaxy.errors import LoweringError
from stratagemdsl.backend.galaxy.bindings import DEFAULT_FILTER, _safe
from stratagemdsl.backend.galaxy.interaction_helpers import _INTERACTION_HELPERS
from stratagemdsl.net import EVENT, IMMEDIATE, POLLED
from stratagemdsl.net.model import NetTransition
from stratagemdsl.net.semantics import SETTLE_LIMIT

OUTCOME_CODE = {"success": 1, "failure": 2}


class ProgramAssembly:
    """Marking globals, enabling/firing functions, dispatch triggers and the MapScript text."""

    # ------------------------------------------------------------ helpers
    def _debug_message(self, text: str, indent: int) -> str:
        # Shown in the map's debug area when a place is entered.
        p = "    " * indent
        escaped = text.replace("\\", "\\\\").replace('"', '\\"')
        return (
            f'{p}UIDisplayMessage(PlayerGroupAll(), c_messageAreaDebug, '
            f'StringToText("{escaped}"));'
        )

    def _m(self, place: str) -> str:
        return self.net_name("m", place)

    def _seen(self, place: str) -> str:
        return self.net_name("seen", place)

    def _phase_action_block(self, n: Phase, indent: int) -> list[str]:
        previous, self._current_phase = self._current_phase, n.id
        try:
            return self._emit_action_block(n.actions, indent)
        finally:
            self._current_phase = previous

    def _players_by_side(self) -> tuple[list[int], list[int]]:
        """Owners of the allied and of the enemy forces/assets (default 1 and 2)."""
        allies = sorted({b.owner for b in self.bound.values() if b.owner and b.side.strip('"') == "ally"})
        enemies = sorted({b.owner for b in self.bound.values() if b.owner and b.side.strip('"') == "enemy"})
        return allies or [1], [p for p in (enemies or [2]) if p not in (allies or [1])]

    def _gameover_lines(self, terminal: str, indent: int) -> list[str]:
        """gameover=True: a success terminal is a victory of the allied players, a failure
        terminal their defeat; the opponents get the opposite result. Latched, so a
        second terminal reached in the same settle cannot overwrite the first."""
        p = "    " * indent
        allies, enemies = self._players_by_side()
        won = self.net.places[terminal].terminal == "success"
        winners, losers = (allies, enemies) if won else (enemies, allies)
        out = [f"{p}if ({self.gameover_global} == false) {{", f"{p}    {self.gameover_global} = true;"]
        out += [f"{p}    GameOver({q}, c_gameOverVictory, true, true);" for q in winners]
        out += [f"{p}    GameOver({q}, c_gameOverDefeat, true, true);" for q in losers]
        return out + [f"{p}}}"]

    def _entry_lines(self, place: str, indent: int, reason: str) -> list[str]:
        """What happens when `place` goes from empty to marked."""
        out = [self._debug_message(reason, indent)]
        if self.gameover_global and self.net.places[place].terminal:
            out.extend(self._gameover_lines(place, indent))
        out.extend(self._phase_entry_timing(place, indent))
        node = self.node_map.get(place)
        if isinstance(node, Phase):
            out.extend(self._phase_action_block(node, indent))
        return out

    def _halt_lines(self, terminal: str, indent: int) -> list[str]:
        """first_wins: latch the outcome and clear every other place."""
        p = "    " * indent
        out = [f"{p}{self.outcome_global} = {OUTCOME_CODE[self.net.places[terminal].terminal]};"]
        for pid in self.net.places:
            if pid == terminal:
                continue
            out.append(f"{p}{self._m(pid)} = 0;")
            out.extend(self._phase_exit_resources(pid, indent))
        return out

    # ------------------------------------------------------ net functions
    def _enabled_expr(self, t: NetTransition) -> str:
        parts: list[str] = []
        if self.outcome_global:
            parts.append(f"({self.outcome_global} == 0)")
        consumed: dict[str, int] = {}
        for a in t.inputs:
            m = self._m(a.place)
            if a.kind == "normal":
                consumed[a.place] = consumed.get(a.place, 0) + a.weight
                parts.append(f"({m} >= {a.weight})")
            elif a.kind == "read":
                parts.append(f"({m} >= {a.weight})")
            else:
                parts.append(f"({m} < {a.weight})")
        for a in t.outputs:
            p = self.net.places[a.place]
            if p.once or p.capacity is None:
                continue   # an arrival at an entered once-place is discarded
            after = f"{self._m(a.place)} - {consumed[a.place]} + {a.weight}" if a.place in consumed \
                else f"{self._m(a.place)} + {a.weight}"
            parts.append(f"(({after}) <= {p.capacity})")
        return " && ".join(parts) if parts else "true"

    def _guard_text(self, t: NetTransition) -> str:
        """Galaxy condition for t's guard (the event context is t's event)."""
        if t.guard_static is True:
            return "true"
        if t.guard_static is False:
            return "false"
        if self.guard_oracle and not t.marking_guard:
            return f"({self.net_name('guard', t.id)} == true)"
        try:
            text, extra = self.emit_transition_guard(t.guard, t.event)
        except LoweringError as e:
            self.transition_kinds[t.id] = {"kind": "error", "message": str(e)}
            raise LoweringError(f"transition '{t.id}' guard cannot lower: {e}") from e
        return " && ".join([*extra, f"({text})"]) if extra else f"({text})"

    def _fire_body(self, t: NetTransition) -> list[str]:
        out: list[str] = []
        for a in t.inputs:
            if a.kind != "normal":
                continue
            m = self._m(a.place)
            out.append(f"    {m} = ({m} - {a.weight});")
            exit_lines = self._phase_exit_resources(a.place, 2)
            if exit_lines:
                out.append(f"    if ({m} == 0) {{")
                out.extend(exit_lines)
                out.append("    }")
        previous, self._event_ctx = self._event_ctx, t.event
        try:
            out.extend(self._emit_action_block(t.actions, 1))
            for i, a in enumerate(t.outputs):
                place = self.net.places[a.place]
                m = self._m(a.place)
                lines: list[str] = []
                srcs = ", ".join(t.consumed) or "-"
                reason = f"{t.origin or t.id}: {srcs} -> {a.place}"
                halt = self.outcome_global and place.terminal
                if place.once:
                    seen = self._seen(a.place)
                    lines.append(f"    if ({seen} == false) {{")
                    lines.append(f"        {seen} = true;")
                    lines.append(f"        {m} = ({m} + {a.weight});")
                    if halt:
                        lines.extend(self._halt_lines(a.place, 2))
                    lines.extend(self._entry_lines(a.place, 2, reason))
                    lines.append("    }")
                else:
                    lines.append(f"    {m} = ({m} + {a.weight});")
                    lines.append(f"    if ({m} == {a.weight}) {{")
                    if halt:
                        lines.extend(self._halt_lines(a.place, 2))
                    lines.extend(self._entry_lines(a.place, 2, reason))
                    lines.append("    }")
                if i > 0 and self.outcome_global and any(self.net.places[b.place].terminal for b in t.outputs[:i]):
                    # An earlier output may have halted the net.
                    lines = [f"    if ({self.outcome_global} == 0) {{"] + ["    " + x for x in lines] + ["    }"]
                out.extend(lines)
        finally:
            self._event_ctx = previous
        return out

    def _net_functions(self) -> list[str]:
        out: list[str] = []
        for t in self.net.transitions:
            out.append(f"bool {self.net_name('en', t.id)} () {{")
            out.append(f"    return {self._enabled_expr(t)};")
            out.append("}")
            out.append("")
        for t in self.net.transitions:
            out.append(f"void {self.net_name('fire', t.id)} () {{")
            out.extend(self._fire_body(t))
            out.append("}")
            out.append("")
        immediates = sorted((t for t in self.net.transitions if t.dispatch == IMMEDIATE), key=lambda t: t.rank)
        out.append("void gf_net_settle () {")
        if immediates:
            out.append("    int lv_steps = 0;")
            out.append(f"    while (lv_steps < {SETTLE_LIMIT}) {{")
            out.append("        lv_steps += 1;")
            for t in immediates:
                self.transition_kinds[t.id] = {"kind": IMMEDIATE, **({"message": t.note} if t.note else {})}
                cond = f"{self.net_name('en', t.id)}()"
                g = self._guard_text(t)
                if g != "true":
                    cond = f"{cond} && {g}"
                out.append(f"        if ({cond}) {{")
                out.append(f"            {self.net_name('fire', t.id)}();")
                out.append("            continue;")
                out.append("        }")
            out.append("        break;")
            out.append("    }")
        out.append("}")
        out.append("")
        out.append("void gf_net_reset () {")
        if self.outcome_global:
            out.append(f"    {self.outcome_global} = 0;")
        if self.gameover_global:
            out.append(f"    {self.gameover_global} = false;")
        for pid, place in self.net.places.items():
            out.append(f"    {self._m(pid)} = {place.initial};")
            if place.once:
                out.append(f"    {self._seen(pid)} = {'true' if place.initial > 0 else 'false'};")
            if place.initial > 0:
                out.append(self._debug_message(f"start: {pid}", 1))
                out.extend(self._phase_entry_timing(pid, 1))
        if self.guard_oracle:
            for t in self.net.transitions:
                if self._uses_oracle(t):
                    out.append(f"    {self.net_name('guard', t.id)} = false;")
        out.append("}")
        return out

    def _uses_oracle(self, t: NetTransition) -> bool:
        return self.guard_oracle and t.guard_static is None and not t.marking_guard

    def _dispatch_body(self, group: list[NetTransition], prefix: list[str]) -> list[str]:
        """Snapshot -> fire by rank -> settle (one event occurrence or tick)."""
        body = [f"    bool lv_c{i};" for i in range(len(group))]
        body += ["    if (!runActions) {", "        return true;", "    }"]
        body += prefix
        for i, t in enumerate(group):
            g = self._guard_text(t)
            cond = f"{self.net_name('en', t.id)}()" + (f" && {g}" if g != "true" else "")
            body.append(f"    lv_c{i} = ({cond});")
        for i, t in enumerate(group):
            body.append(f"    if (lv_c{i} && {self.net_name('en', t.id)}()) {{")
            body.append(f"        {self.net_name('fire', t.id)}();")
            body.append("    }")
        body.append("    gf_net_settle();")
        return body

    def _start_environment_actions(self) -> list[str]:
        """Entry actions of initially marked phases, then the first settle."""
        lines: list[str] = []
        for nid in self.s.plan.start:
            n = self.node_map.get(nid)
            if isinstance(n, Phase):
                lines.extend(self._phase_action_block(n, 1))
        lines.append("    gf_net_settle();")
        return lines

    # ------------------------------------------------------------- setup
    def _setup_lines(self) -> list[str]:
        b = self.r.bindings.get("__setup__")
        if b is None or not isinstance(b.value, BindingCall) or b.value.name != "setup":
            return []
        out: list[str] = []
        for arg in b.value.args:
            items = arg.value if isinstance(arg.value, list) else [arg.value]
            for item in items:
                if not isinstance(item, BindingCall):
                    continue
                name = item.name
                if name == "minerals":
                    player = int(self.r.named(item, "player")); value = int(self.r.named(item, "value"))
                    out.append(f"    PlayerModifyPropertyInt({player}, c_playerPropMinerals, c_playerPropOperSetTo, {value});")
                elif name == "supplies_made":
                    player = int(self.r.named(item, "player")); value = float(self.r.named(item, "value"))
                    out.append(f"    PlayerModifyPropertyFixed({player}, c_playerPropSuppliesMade, c_playerPropOperSetTo, {value});")
                elif name == "upgrade":
                    player = int(self.r.named(item, "player")); up = self.r.named(item, "name"); level = int(self.r.named(item, "level", 1))
                    out.append(f'    libNtve_gf_SetUpgradeLevelForPlayer({player}, "{up}", {level});')
                elif name == "creep":
                    region = self.r.named(item, "region"); enabled = bool(self.r.named(item, "enabled", True))
                    rb = self.bound.get(str(region))
                    if rb is not None and rb.decl.kind == "region" and rb.region_kind != "circle":
                        cc, rr = self._region_geom(str(region))
                        out.append(f"    CreepModify({cc}, {rr}, {'true' if enabled else 'false'}, false);")
                        continue
                    if rb is None or rb.decl.kind != "region" or rb.region_center is None or rb.region_radius is None:
                        raise LoweringError("creep setup requires a bound circle region")
                    out.append(f"    CreepModify({rb.region_center.emit()}, {rb.region_radius}, {'true' if enabled else 'false'}, false);")
                elif name == "remove_behavior":
                    asset = str(self.r.named(item, "asset")); behavior = str(self.r.named(item, "name"))
                    out.append(f'    UnitBehaviorRemove(UnitGroupUnit({self._group(asset)}, 1), "{behavior}", 1);')
                elif name == "tech_requirements":
                    player = int(self.r.named(item, "player")); enabled = bool(self.r.named(item, "enabled", False))
                    out.append(f"    TechTreeRequirementsEnable({player}, {'true' if enabled else 'false'});")
        out.extend(ext.setup_lines(self, b.value))
        return out

    def _poll_period(self) -> float:
        setup = self.r.bindings.get("__setup__")
        value = self.r.named(setup.value, "poll_period", 1.0) if setup and isinstance(setup.value, BindingCall) else 1.0
        return self.r._require_positive_number(value, "poll_period")

    # --------------------------------------------------------------- emit
    def emit(self) -> str:
        for fixed in ("gt_MapInit", "gt_Reset"):
            for suffix in ("", "_Func", "_Init"):
                self._used_global_names.add(fixed + suffix)
        for fixed in ("gf_net_settle", "gf_net_reset"):
            self._used_global_names.add(fixed)

        globals_: list[str] = []
        init_globals: list[str] = []
        spawn: list[str] = []

        if self.outcome_global:
            globals_.append(f"int {self.outcome_global};")
            init_globals.append(f"    {self.outcome_global} = 0;")
        if self.gameover_global:
            globals_.append(f"bool {self.gameover_global};")
            init_globals.append(f"    {self.gameover_global} = false;")
        for pid, place in self.net.places.items():
            globals_.append(f"int {self._m(pid)};")
            init_globals.append(f"    {self._m(pid)} = 0;")
            if place.once:
                globals_.append(f"bool {self._seen(pid)};")
                init_globals.append(f"    {self._seen(pid)} = false;")
        if self.guard_oracle:
            for t in self.net.transitions:
                if self._uses_oracle(t):
                    globals_.append(f"bool {self.net_name('guard', t.id)};")
                    init_globals.append(f"    {self.net_name('guard', t.id)} = false;")

        for name, b in self.bound.items():
            if b.decl.kind in {"force", "asset"}:
                if b.dynamic_owner is not None:
                    continue   # dynamic bindings are queried on demand
                globals_.append(f"unitgroup {b.global_name};")
                init_globals.append(f"    {b.global_name} = UnitGroupEmpty();")
                spawn.append(f"    {b.global_name} = UnitGroupEmpty();")
                if bool(b.decl.properties.get("initial", True)):
                    for c in b.spawn_components:
                        spawn.extend(c.spawn_lines("    ", b.global_name))
            elif b.decl.kind == "region":
                globals_.append(f"region {b.global_name};")
                init_globals.extend(self._region_init_lines(b))
            elif b.decl.kind == "route":
                self.notes.append(f"route preserved only in strategic IR: {name}")

        v04_spawn_at = len(spawn)
        spawn.append("    gf_net_reset();")

        monitor_triggers: list[tuple[str, list[str], list[str], list[str]]] = []
        for spec in self.counter_specs.values():
            self._used_global_names.add(spec.trigger_name)
            globals_.append(f"int {spec.global_name};")
            init_globals.append(f"    {spec.global_name} = 0;")
            spawn.append(f"    {spec.global_name} = 0;")
            if spec.seen_global:
                globals_.append(f"unitgroup {spec.seen_global};")
                init_globals.append(f"    {spec.seen_global} = UnitGroupEmpty();")
                spawn.append(f"    {spec.seen_global} = UnitGroupEmpty();")
            events = [f"    TriggerAddEventUnitDied({spec.trigger_name}, null);"]
            guards = self._event_identity_guards(spec.force)
            guards.append(self._event_position_in_region_guard(spec.region))
            acts = [f"    {spec.global_name} += 1;"]
            if spec.seen_global:
                guards.append(f"UnitGroupHasUnit({spec.seen_global}, EventUnit()) == false")
                acts.append(f"    UnitGroupAdd({spec.seen_global}, EventUnit());")
            monitor_triggers.append((spec.trigger_name, events, guards, acts))

        # ---- dispatch triggers: one per distinct event, one periodic tick
        dispatch_triggers: list[tuple[str, list[str], list[str], list[str]]] = []
        groups: dict[tuple, list[NetTransition]] = {}
        for t in sorted(self.net.transitions, key=lambda x: x.rank):
            if t.dispatch == EVENT:
                groups.setdefault(t.trigger, []).append(t)
        for key, group in groups.items():
            lead = group[0]
            base = f"gt_{_safe(lead.id)}" if len(group) == 1 else f"gt_evt_{_safe(lead.event.name)}_{_safe(lead.id)}"
            gt = self._unique_trigger_name(base)
            events, identity_guards = self.emit_event_registration(lead.event, gt)
            for t in group:
                self.transition_kinds[t.id] = {"kind": EVENT, "trigger": gt}
            if len(group) > 1:
                self.notes.append(
                    f"event {lead.event.name} drives {len(group)} transitions "
                    f"({', '.join(t.id for t in group)}); one dispatcher fires the enabled ones by rank")
            dispatch_triggers.append((gt, events, identity_guards, self._dispatch_body(group, [])))

        polled = sorted((t for t in self.net.transitions if t.dispatch == POLLED), key=lambda t: t.rank)
        if polled:
            gt = self._unique_trigger_name("gt_net_tick")
            for t in polled:
                self.transition_kinds[t.id] = {"kind": POLLED, "trigger": gt, **({"message": t.note} if t.note else {})}
            events = [f"    TriggerAddEventTimePeriodic({gt}, {self._poll_period()!r}, c_timeGame);"]
            dispatch_triggers.append((gt, events, [], self._dispatch_body(polled, ext.poll_prefix_lines(self))))

        net_functions = self._net_functions()   # after dispatch: guard errors are recorded per transition
        setup_actions = self._setup_lines()
        start_actions = self._start_environment_actions()
        for phase, gv in self.phase_clock_specs.items():
            globals_.append(f"fixed {gv};")
            init_globals.append(f"    {gv} = 0.0;")
        for gv in self.timer_specs.values():
            globals_.append(f"timer {gv};")
            init_globals.append(f"    {gv} = TimerCreate();")
        for name, b in self.bound.items():
            if not b.adopt_types:
                continue
            gt = self._unique_trigger_name(f"gt_adopt_{_safe(name)}")
            types = " || ".join(f"UnitGetType(EventUnitCreatedUnit()) == {ext.gs(t)}" for t in b.adopt_types)
            monitor_triggers.append((gt, [f"    TriggerAddEventUnitCreated({gt}, null, null, null);"],
                [f"UnitGetOwner(EventUnitCreatedUnit()) == {b.owner}", f"({types})"],
                [f"    UnitGroupAdd({b.global_name}, EventUnitCreatedUnit());"]))
        # An attached region must follow its roster even when nothing polls.
        if self.ext_state.attached or self.ext_state.revealers:
            gt = self._unique_trigger_name("gt_attached_regions")
            updates = ext.poll_prefix_lines(self)
            for gv in self.ext_state.revealers.values():
                updates += [f"    if ({gv} != null) {{", f"        VisRevealerUpdate({gv});", "    }"]
            monitor_triggers.append((gt, [f"    TriggerAddEventTimePeriodic({gt}, {self._poll_period()!r}, c_timeGame);"], [], updates))
        cleanup = []
        for node in self.net.places:
            cleanup.extend(self._phase_exit_resources(node))
        spawn[0:0] = cleanup
        v04_spawn_at += len(cleanup)
        v04_decl, v04_init = ext.global_lines(self)
        globals_.extend(v04_decl)
        init_globals.extend(v04_init)
        init_globals.extend(f"    {gv} = null;" for gv in self.ext_state.revealers.values())
        spawn[v04_spawn_at:v04_spawn_at] = ext.spawn_lines(self)

        lines = [
            'include "TriggerLibs/NativeLib"',
            '',
            '// Generated by StratagemDSL v0.6: the plan runs as a Petri-net token game.',
            f'// net: {len(self.net.places)} places, {len(self.net.transitions)} transitions',
            '',
            'void InitLibs () {',
            '    libNtve_InitLib();',
            '}',
            '',
        ]
        lines.extend(globals_)
        lines.extend(['', 'void InitGlobals () {'])
        lines.extend(init_globals)
        lines.extend(['}', ''])
        for name, body in {**_INTERACTION_HELPERS, **ext.H}.items():
            if name in self._helpers_used:
                lines.extend(body)
                lines.append("")
        lines.extend(net_functions)
        lines.extend(['', 'void gf_Spawn ();', '', 'trigger gt_MapInit;', 'trigger gt_Reset;'])
        lines.extend([f"trigger {gt};" for gt, *_ in monitor_triggers])
        lines.extend([f"trigger {gt};" for gt, *_ in dispatch_triggers])
        lines.extend(['', 'void gf_Spawn () {'])
        lines.extend(spawn)
        lines.extend([
            '}',
            '',
            'bool gt_MapInit_Func (bool testConds, bool runActions) {',
            '    if (!runActions) {',
            '        return true;',
            '    }',
            '    VisEnable(c_visTypeFog, false);',
            '    VisEnable(c_visTypeMask, false);',
            '    TechTreeRequirementsEnable(1, false);',
            '    TechTreeRequirementsEnable(2, false);',
        ])
        lines.extend(self._region_build_lines())
        lines.append('    gf_Spawn();')
        lines.extend(setup_actions)
        lines.extend(start_actions)
        lines.extend([
            '    return true;',
            '}',
            '',
            'void gt_MapInit_Init () {',
            '    gt_MapInit = TriggerCreate("gt_MapInit_Func");',
            '    TriggerAddEventMapInit(gt_MapInit);',
            '}',
            '',
            'bool gt_Reset_Func (bool testConds, bool runActions) {',
            '    if (testConds) {',
            f'        if (!((UnitGroupCount(UnitGroup(null, 1, RegionEntireMap(), {DEFAULT_FILTER}, 0), c_unitCountAlive) == 0) && (UnitGroupCount(UnitGroup(null, 2, RegionEntireMap(), {DEFAULT_FILTER}, 0), c_unitCountAlive) == 0))) {{',
            '            return false;',
            '        }',
            '    }',
            '    if (!runActions) {',
            '        return true;',
            '    }',
            '    gf_Spawn();',
        ])
        lines.extend(setup_actions)
        lines.extend(start_actions)
        lines.extend([
            '    return true;',
            '}',
            '',
            'void gt_Reset_Init () {',
            '    gt_Reset = TriggerCreate("gt_Reset_Func");',
            '    TriggerAddEventUnitDied(gt_Reset, null);',
            '}',
            '',
        ])

        def trigger_text(gt, events, guards, acts):
            out = [f"bool {gt}_Func (bool testConds, bool runActions) {{"]
            decls = [a for a in acts if a.startswith("    bool lv_c")]
            rest = [a for a in acts if not a.startswith("    bool lv_c")]
            out.extend(decls)
            if guards:
                out.append('    if (testConds) {')
                for g in guards:
                    out.extend([f"        if (!({g})) {{", '            return false;', '        }'])
                out.append('    }')
            if not any(a.strip() == "if (!runActions) {" for a in rest):
                rest = ['    if (!runActions) {', '        return true;', '    }'] + rest
            out.extend(rest)
            out.extend(['    return true;', '}', '', f"void {gt}_Init () {{", f'    {gt} = TriggerCreate("{gt}_Func");'])
            out.extend(events)
            out.extend(['}', ''])
            return out

        for item in monitor_triggers:
            lines.extend(trigger_text(*item))
        for item in dispatch_triggers:
            lines.extend(trigger_text(*item))

        lines.extend(['void InitTriggers () {', '    gt_MapInit_Init();', '    gt_Reset_Init();'])
        lines.extend([f"    {gt}_Init();" for gt, *_ in monitor_triggers])
        lines.extend([f"    {gt}_Init();" for gt, *_ in dispatch_triggers])
        lines.extend(['}', '', 'void InitMap () {', '    InitLibs();', '    InitGlobals();', '    InitTriggers();', '}', ''])
        setup = self.r.bindings.get("__setup__")
        if setup and isinstance(setup.value, BindingCall) and self.r.named(setup.value, "fog", False):
            lines = [line.replace("VisEnable(c_visTypeFog, false)", "VisEnable(c_visTypeFog, true)").replace("VisEnable(c_visTypeMask, false)", "VisEnable(c_visTypeMask, true)") for line in lines]
        return "\n".join(lines)
