"""A plan-driven stand-in for StarCraft II: the map's script, toy combat and ground paths.

`ToySim` only moves units. `PlanSim` also plays the enemy side the way the
generated map does: it runs the plan's Petri net (`net.TokenGame`) on the
events of a small world simulation, and the enemy orders in phase `do`
blocks and transition actions are carried out when the net enters/fires
them (allied orders too with ``oracle=True``, like `strat pack --oracle`).
A terminal place ends the game (`strat pack --gameover`): success is a
victory for the allied player, failure a defeat.

The world is deliberately simple:

* ground units walk A* paths over the base map's cliff levels and ramps
  (`views.routes.Grid`), air units fly straight; no collisions;
* combat is flat DPS from `play.unitdata` (shields first, then hit points
  less armour per hit; no splash, no bonus damage), units auto-acquire
  enemies in range, chase a little when idle, and answer an attacker;
  burrowed units are untargetable and inert
  (no detection);
* vision: a unit sees `sight` cells; `visible_tags(player)` gives what a
  player sees (the frame for agents is filtered by it when ``fog=True``).

Events fed to the net: enter/leave (per unit crossing a circular region),
unit_died, unit_attacked (target, attacker; once per pair and tick),
ability_cast/ability_completed (allied abilities given as orders), timer
(seconds since the phase was entered); then a poll tick for world guards.
Guards are evaluated by `play.worldguards` with full knowledge.

It implements the `play.game.Backend` protocol, so `strat play --dry-run
--sim plan` can use it, and `llm_pysc2.stratagem.fake_sc2` builds a
protocol-level StarCraft II stand-in on top of it.
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from typing import Optional

from stratagemdsl.core.model import CallExpr, NameExpr, NumberExpr, Phase, StringExpr, Strategy
from stratagemdsl.net import StepLog, TokenGame, build_net
from stratagemdsl.packaging.terrain import MapProfile
from stratagemdsl.play.game import LOOPS_PER_SECOND, Frame, Order, Unit
from stratagemdsl.play.scenario import Scenario, build_scenario
from stratagemdsl.play.unitdata import (BURROWED_NAME, MORPHS, UNBURROWED_NAME, UnitStats, armor_of, hit_of,
                                        stats_of)
from stratagemdsl.play.worldguards import truth, unsupported_calls
from stratagemdsl.views.routes import FOOTPRINT, Grid, Location

STEP_LOOPS = 8
OUTCOME_RESULT = {1: "victory", 2: "defeat"}
IDLE_CHASE = 3.0       # an idle unit walks this far beyond its range toward an enemy it saw
LEASH = 8.0            # ... but not farther than this from where it became idle


@dataclass
class SimOrder:
    kind: str                                   # move | attack_pt | attack_unit | attack_group | hold | patrol
    point: Optional[tuple[float, float]] = None
    target_tag: Optional[int] = None
    group: Optional[str] = None                 # force name for attack_group
    source: str = ""                            # "agent" | "script"


@dataclass
class SimUnit:
    tag: int
    unit_type: str
    owner: int
    x: float
    y: float
    stats: UnitStats
    hp: float
    shield: float
    energy: float = 0.0
    force: Optional[str] = None
    order: Optional[SimOrder] = None
    queue: list[SimOrder] = field(default_factory=list)
    burrowed: bool = False
    alive: bool = True
    facing: float = 0.0
    anchor: Optional[tuple[float, float]] = None
    path: list[tuple[float, float]] = field(default_factory=list)
    path_goal: Optional[tuple[float, float]] = None
    path_age: int = 0
    attacked_by: Optional[int] = None
    target: Optional[int] = None                 # tag currently fired at (for reports)
    weapon_cooldown: float = 0.0
    regions: frozenset = frozenset()

    @property
    def structure(self) -> bool:
        return self.stats.structure

    @property
    def air(self) -> bool:
        return self.stats.air

    @property
    def radius(self) -> float:
        return self.stats.radius


class PlanSim:
    def __init__(self, strategy: Strategy, profile: MapProfile, *, scenario: Optional[Scenario] = None,
                 oracle: bool = False, max_loops: int = 22 * 60 * 15, player_id: Optional[int] = None,
                 fog: bool = True, step_loops: int = STEP_LOOPS, seed: Optional[int] = None):
        self.strategy = strategy
        self.profile = profile
        self.sc = scenario or build_scenario(strategy, profile)
        self.oracle = oracle
        self.max_loops = max_loops
        self.player_id = player_id or self.sc.ally_owner
        self.fog = fog
        self.step_loops = step_loops
        self.rng = random.Random(seed)
        self.net = build_net(strategy)
        self.game = TokenGame(self.net)
        self.grid = Grid(profile)
        self._paths: dict[tuple, Optional[list[tuple[int, int]]]] = {}
        phases = {n.id: n for n in strategy.plan.nodes if isinstance(n, Phase)}
        self.phase_of = {pid: phases[p.origin] for pid, p in self.net.places.items()
                         if p.kind == "phase" and p.origin in phases}
        self.side = {e.name: str(e.properties.get("side", "")).strip('"') for e in strategy.world}
        self.kind = {e.name: e.kind for e in strategy.world}
        self.regions: dict[str, Location] = dict(self.sc.regions)
        self.event_keys = [k for k in self.game.groups if k[0] == "event"]
        self.notes: set[str] = set()
        for t in self.net.transitions:
            bad = unsupported_calls(t.guard, self.net.derived)
            if bad:
                self.notes.add(f"guard of {t.origin or t.id} uses {sorted(bad)}: treated as unknown (false)")
        self.units: list[SimUnit] = []

    # ================================================================ setup
    def reset(self) -> Frame:
        self.loop = 0
        self.units, self.by_tag = [], {}
        self.events: list[dict] = []          # world events (enter/leave/died/attacked/ability)
        self.history: list[dict] = []         # net activity: fired transitions, entered/left places, orders
        self.kills_in: dict[tuple[str, str], int] = {}
        self.entered_at: dict[str, int] = {}
        self.timer_fired: set[tuple] = set()
        self._pending: list[tuple[str, tuple, str]] = []
        self.seen_structures: dict[int, set[int]] = {}
        tag = 0x100000001
        for f in self.sc.forces.values():
            if f.spawn is None or f.owner is None:
                continue
            k = 0
            for unit_type, n in (f.composition or [(f.unit_types[0] if f.unit_types else "Marine", max(1, f.count))]):
                for _ in range(n if f.kind == "force" else 1):
                    st = stats_of(unit_type, structure_hint=f.kind == "asset" or unit_type in FOOTPRINT)
                    if f.kind == "asset" or st.structure:
                        x, y = f.spawn
                    else:
                        k += 1
                        ang = 2.39996 * k + self.rng.uniform(-0.3, 0.3)    # seed varies the formation a little
                        r = 0.7 * math.sqrt(k) + self.rng.uniform(0.0, 0.2)
                        x, y = self._walkable_near(f.spawn[0] + r * math.cos(ang), f.spawn[1] + r * math.sin(ang),
                                                   f.spawn)
                    u = SimUnit(tag, unit_type, f.owner, x, y, st, st.hp, st.shield, st.energy, force=f.name)
                    u.anchor = (x, y)
                    self.units.append(u)
                    self.by_tag[tag] = u
                    tag += 0x40000
        for u in self.units:
            u.regions = self._regions_of(u)
        log = StepLog()
        self.state = self.game.initial(log)
        self._apply(log, "start")
        return self._frame()

    def _walkable_near(self, x: float, y: float, fallback: tuple[float, float]) -> tuple[float, float]:
        if self.profile.walkable(x, y):
            return (x, y)
        p = self.profile.nearest_valid(x, y, max_radius=4)
        return p or fallback

    # ============================================================== protocol
    def step(self, orders: list[Order]) -> Frame:
        self.issue(orders)
        self.advance(self.step_loops)
        return self._frame()

    def close(self) -> None:
        pass

    @property
    def outcome(self) -> Optional[str]:
        return OUTCOME_RESULT.get(self.state.outcome)

    @property
    def done(self) -> bool:
        return self.outcome is not None or self.loop >= self.max_loops

    def result(self) -> Optional[str]:
        if self.outcome:
            return self.outcome
        return "timeout" if self.loop >= self.max_loops else None

    # ================================================================ orders
    def issue(self, orders: list[Order], owner: Optional[int] = None, *, source: str = "agent") -> None:
        owner = self.player_id if owner is None else owner
        for o in orders:
            queued = bool(o.meta.get("queued")) if o.meta else False
            for t in o.tags:
                u = self.by_tag.get(t)
                if u is None or not u.alive or u.owner != owner:
                    continue
                self.order_unit(u, o, queued=queued, source=source)

    def order_unit(self, u: SimUnit, o: Order, *, queued: bool = False, source: str = "agent") -> None:
        kind = o.kind
        if kind == "ability":
            self._ability(u, str(o.meta.get("ability", "")), o)
            return
        if kind in ("stop", "hold"):
            u.order, u.queue, u.path = (SimOrder("hold", source=source) if kind == "hold" else None), [], []
            u.anchor = (u.x, u.y)
            return
        if u.burrowed or u.stats.speed <= 0 and kind in ("move",):
            return
        so = SimOrder(kind, point=o.point, target_tag=o.target_tag, group=o.meta.get("group") if o.meta else None,
                      source=source)
        if queued and u.order is not None:
            u.queue.append(so)
        else:
            u.order, u.queue, u.path, u.path_goal = so, [], [], None

    def _ability(self, u: SimUnit, ability: str, o: Order) -> None:
        key = ability.lower().replace("_", "")
        for (frm, word), to in MORPHS.items():
            if u.unit_type == frm and word in key:
                self._morph(u, to)
                self._event("ability_completed", (u.force,), ability)
                return
        if "blink" in key and o.point is not None:
            dx, dy = o.point[0] - u.x, o.point[1] - u.y
            d = math.hypot(dx, dy)
            k = min(1.0, 8.0 / d) if d > 0 else 0.0
            nx, ny = u.x + dx * k, u.y + dy * k
            if self.profile.walkable(nx, ny):
                u.x, u.y, u.path, u.path_goal = nx, ny, [], None
        elif "burrowdown" in key and not u.air and not u.structure:
            u.burrowed, u.order, u.queue, u.path = True, None, [], []
            u.unit_type = BURROWED_NAME.get(u.unit_type, u.unit_type)
        elif "burrowup" in key and u.burrowed:
            u.burrowed = False
            u.unit_type = UNBURROWED_NAME.get(u.unit_type, u.unit_type)
        elif "stim" in key and u.hp > 10:
            u.hp -= 10
        self._event("ability_cast", (u.force,), ability)
        self._event("ability_completed", (u.force,), ability)

    def _morph(self, u: SimUnit, to: str) -> None:
        st = stats_of(to)
        frac = u.hp / u.stats.hp if u.stats.hp else 1.0
        u.unit_type, u.stats = to, st
        u.hp = max(1.0, st.hp * frac)
        u.burrowed = to.endswith("Burrowed") and to not in ("LurkerBurrowed", "WidowMineBurrowed")
        u.order, u.queue, u.path = None, [], []

    # ============================================================= the world
    def advance(self, loops: int) -> None:
        if self.done:
            return
        dt = loops / LOOPS_PER_SECOND
        alive = [u for u in self.units if u.alive]
        for u in alive:
            self._act(u, dt)
        self.loop += loops
        # deaths
        for u in alive:
            if u.alive and u.hp <= 0:
                u.alive = False
                regs = self._regions_of(u)
                for r in regs:
                    if u.force:
                        self.kills_in[(u.force, r)] = self.kills_in.get((u.force, r), 0) + 1
                if u.force:
                    self._event("unit_died", (u.force,), "")
                self.by_tag.pop(u.tag, None)
        self.units = [u for u in self.units if u.alive]
        # region crossings
        for u in self.units:
            if u.structure or not u.force:
                continue
            now = self._regions_of(u)
            for r in sorted(now - u.regions):
                self._event("enter", (u.force, r), "")
            for r in sorted(u.regions - now):
                self._event("leave", (u.force, r), "")
            u.regions = now
        self._run_net()

    def _act(self, u: SimUnit, dt: float) -> None:
        u.target = None
        u.weapon_cooldown = max(0.0, u.weapon_cooldown - dt)
        if u.burrowed:
            return
        o = u.order
        if o is None and u.queue:
            o = u.order = u.queue.pop(0)
        if o is None or o.kind == "hold":
            enemy = self._enemy_in_reach(u, 0.0)
            if enemy is None and o is None and not u.structure and u.stats.speed > 0:
                enemy = self._idle_response(u)
                if enemy is not None and not self._in_range(u, enemy):
                    self._walk_to(u, (enemy.x, enemy.y), dt)
                    return
            if enemy is not None and self._in_range(u, enemy):
                self._fire(u, enemy, dt)
            return
        if o.kind == "move":
            if self._walk_to(u, o.point, dt, stop=0.6):
                self._finish(u)
            return
        if o.kind == "attack_pt":
            enemy = self._enemy_in_reach(u, 2.0)
            if enemy is not None:
                if self._in_range(u, enemy):
                    self._fire(u, enemy, dt)
                else:
                    self._walk_to(u, (enemy.x, enemy.y), dt)
                return
            if self._walk_to(u, o.point, dt, stop=0.8):
                self._finish(u)
            return
        if o.kind in ("attack_unit", "attack_group"):
            if o.kind == "attack_unit":
                tgt = self.by_tag.get(o.target_tag)
                tgt = tgt if tgt is not None and tgt.alive and self._can_hit(u, tgt) else None
            else:
                members = [v for v in self.units if v.alive and v.force == o.group and self._targetable(v)
                           and self._can_hit(u, v)]
                tgt = min(members, key=lambda v: self._dist(u, v)) if members else None
            if tgt is None:
                self._finish(u)
                return
            if self._in_range(u, tgt):
                self._fire(u, tgt, dt)
            else:
                self._walk_to(u, (tgt.x, tgt.y), dt)
            return
        self._finish(u)

    def _finish(self, u: SimUnit) -> None:
        u.order, u.path, u.path_goal = (u.queue.pop(0) if u.queue else None), [], None
        u.anchor = (u.x, u.y)

    # ------------------------------------------------------------- combat
    def _hostile(self, a: SimUnit, b: SimUnit) -> bool:
        return a.owner != b.owner and a.owner in (1, 2) and b.owner in (1, 2)

    def _targetable(self, v: SimUnit) -> bool:
        return v.alive and not v.burrowed

    def _can_hit(self, u: SimUnit, v: SimUnit) -> bool:
        return (u.stats.dps_air > 0) if v.air else (u.stats.dps_ground > 0)

    def _range(self, u: SimUnit, v: SimUnit) -> float:
        return u.stats.range_air if v.air else u.stats.range_ground

    def _dist(self, u: SimUnit, v: SimUnit) -> float:
        return math.hypot(u.x - v.x, u.y - v.y)

    def _in_range(self, u: SimUnit, v: SimUnit) -> bool:
        return self._dist(u, v) <= self._range(u, v) + u.radius + v.radius + 0.1

    def _enemy_in_reach(self, u: SimUnit, extra: float) -> Optional[SimUnit]:
        best, bd = None, None
        for v in self.units:
            if not (v.alive and self._hostile(u, v) and self._targetable(v) and self._can_hit(u, v)):
                continue
            d = self._dist(u, v) - u.radius - v.radius - self._range(u, v)
            if d <= extra and (bd is None or (v.structure, d) < (best.structure, bd)):
                best, bd = v, d
        return best

    def _idle_response(self, u: SimUnit) -> Optional[SimUnit]:
        anchor = u.anchor or (u.x, u.y)
        if math.hypot(u.x - anchor[0], u.y - anchor[1]) > LEASH:
            return None
        if u.attacked_by is not None:
            a = self.by_tag.get(u.attacked_by)
            u.attacked_by = None
            if a is not None and a.alive and self._targetable(a) and self._can_hit(u, a):
                return a
        return self._enemy_in_reach(u, IDLE_CHASE)

    def _fire(self, u: SimUnit, v: SimUnit, dt: float) -> None:
        dps = u.stats.dps_air if v.air else u.stats.dps_ground
        if dps <= 0:
            return
        u.target = v.tag
        u.facing = math.atan2(v.y - u.y, v.x - u.x)
        u.weapon_cooldown = 0.5
        dmg = dps * dt
        if v.shield > 0:
            s = min(v.shield, dmg)
            v.shield -= s
            dmg -= s
        if dmg > 0:     # armour takes a flat amount off every hit (at least 0.5 damage stays)
            hit = hit_of(u.unit_type)
            dmg *= max(0.5, hit - armor_of(v.unit_type, v.structure)) / hit
        v.hp -= dmg
        v.attacked_by = u.tag
        if v.force:
            self._event("unit_attacked", (v.force, u.force or ""), "", dedupe=True)

    # ----------------------------------------------------------- movement
    def _walk_to(self, u: SimUnit, goal: tuple[float, float], dt: float, stop: float = 0.0) -> bool:
        """Advance along a path toward goal; True when within `stop` of it."""
        if u.structure or u.stats.speed <= 0:
            return True
        if math.hypot(goal[0] - u.x, goal[1] - u.y) <= max(stop, 0.05):
            return True
        if (u.path_goal is None or math.hypot(goal[0] - u.path_goal[0], goal[1] - u.path_goal[1]) > 1.5
                or not u.path or u.path_age > 40):
            u.path = self._path(u, goal)
            u.path_goal, u.path_age = goal, 0
        u.path_age += 1
        budget = u.stats.speed * dt
        while budget > 1e-9 and u.path:
            wx, wy = u.path[0]
            d = math.hypot(wx - u.x, wy - u.y)
            if d <= budget:
                u.x, u.y = wx, wy
                budget -= d
                u.path.pop(0)
            else:
                u.facing = math.atan2(wy - u.y, wx - u.x)
                u.x += (wx - u.x) * budget / d
                u.y += (wy - u.y) * budget / d
                budget = 0
        return math.hypot(goal[0] - u.x, goal[1] - u.y) <= max(stop, 0.05) or not u.path

    def _path(self, u: SimUnit, goal: tuple[float, float]) -> list[tuple[float, float]]:
        if u.air:
            return [goal]
        start = self.grid.snap(u.x, u.y, radius=2)
        end = self.grid.snap(goal[0], goal[1], radius=3)
        if start is None or end is None:
            return [goal]
        key = (start, end)
        if key not in self._paths:
            if len(self._paths) > 4000:
                self._paths.clear()
            self._paths[key] = self.grid.astar(start, Location("goal", end[0] + 0.5, end[1] + 0.5), 0.0)
        cells = self._paths[key]
        if not cells:
            return [goal]
        pts = [(i + 0.5, j + 0.5) for i, j in cells[1:]]
        # straighten: keep turning points only
        out: list[tuple[float, float]] = []
        for k, p in enumerate(pts):
            if 0 < k < len(pts) - 1:
                a, b = pts[k - 1], pts[k + 1]
                if (p[0] - a[0], p[1] - a[1]) == (b[0] - p[0], b[1] - p[1]):
                    continue
            out.append(p)
        out.append(goal)
        return out

    # ------------------------------------------------------------ regions
    def _regions_of(self, u: SimUnit) -> frozenset:
        return frozenset(r for r, loc in self.regions.items()
                         if loc.radius > 0 and math.hypot(u.x - loc.x, u.y - loc.y) <= loc.radius)

    # ================================================================ net
    def _event(self, name: str, args: tuple, extra: str, dedupe: bool = False) -> None:
        item = (name, tuple(a for a in args), extra)
        if dedupe and item in self._pending:
            return
        self._pending.append(item)
        rec = {"loop": self.loop, "event": name, "args": list(args)}
        if extra:
            rec["detail"] = extra
        if not dedupe or name != "unit_attacked" or not self.events or self.events[-1] != rec:
            self.events.append(rec)

    def _matches(self, key: tuple, occ: tuple) -> bool:
        evname, args = key[1]
        name, names, extra = occ
        if evname != name:
            return False
        named = [v for kind, v in args if kind == "name"]
        strs = [v for kind, v in args if kind == "str"]
        if len(named) > len(names) or list(names[:len(named)]) != named:
            return False
        if strs and not any(s.lower().replace("_", "") in extra.lower().replace("_", "") for s in strs):
            return False
        return name not in ("unit_attacked",) or len(named) <= len(names)

    def _run_net(self) -> None:
        pending, self._pending = self._pending, []
        if self.state.outcome:
            return
        oracle = self._oracle
        for occ in pending:
            for key in self.event_keys:
                if self._matches(key, occ):
                    log = StepLog()
                    self.state = self.game.step(self.state, key, oracle, log)
                    self._apply(log, f"{occ[0]}({', '.join(a for a in occ[1] if a)})")
                    if self.state.outcome:
                        return
        for key in self.event_keys:   # timers
            evname, args = key[1]
            if evname != "timer" or len(args) < 2:
                continue
            place, secs = args[0][1], args[1][1]
            entered = self.entered_at.get(place)
            if entered is None or (key, entered) in self.timer_fired:
                continue
            if (self.loop - entered) / LOOPS_PER_SECOND >= float(secs):
                self.timer_fired.add((key, entered))
                log = StepLog()
                self.state = self.game.step(self.state, key, oracle, log)
                self._apply(log, f"timer({place}, {secs})")
                if self.state.outcome:
                    return
        if ("poll",) in self.game.groups:
            log = StepLog()
            self.state = self.game.step(self.state, ("poll",), oracle, log)
            self._apply(log, "poll")

    def _oracle(self, t) -> bool:
        return truth(t.guard, self.game.marking_dict(self.state), self.net.derived, self) is True

    def _apply(self, log: StepLog, cause: str) -> None:
        if not (log.fired or log.entered or log.left):
            return
        rec = {"loop": self.loop, "cause": cause, "fired": [], "entered": list(log.entered), "left": list(log.left),
               "orders": []}
        for p in log.left:
            self.entered_at.pop(p, None)
        for tid in log.fired:
            t = self.game.ts[tid].t
            if t.origin:
                rec["fired"].append(t.origin)
            if t.actions:
                for call in t.actions.actions:
                    rec["orders"] += self._run_action(call)
        for p in log.entered:
            self.entered_at[p] = self.loop
            ph = self.phase_of.get(p)
            if ph is not None and ph.actions:
                for call in ph.actions.actions:
                    rec["orders"] += self._run_action(call)
        self.history.append(rec)

    # -------------------------------------------------------- script orders
    def _run_action(self, call: CallExpr) -> list[str]:
        if not call.args or not isinstance(call.args[0], NameExpr):
            return []
        actor = call.args[0].name
        if self.side.get(actor) == "ally" and not self.oracle:
            return []            # the agent's job
        members = [u for u in self.units if u.alive and u.force == actor]
        if not members:
            return []
        n = call.name
        target = call.args[1].name if len(call.args) > 1 and isinstance(call.args[1], NameExpr) else None
        text = f"{n}({actor}{', ' + target if target else ''})"
        owner = members[0].owner
        if n in ("attack", "retarget") and target:
            if self.kind.get(target) == "region":
                kind = "move" if n == "retarget" else "attack_pt"
                self.issue([Order(kind, [u.tag for u in members], point=self._loc(target))], owner, source="script")
            elif n == "retarget" and self.side.get(target) == self.side.get(actor):
                self.issue([Order("move", [u.tag for u in members], point=self._loc(target))], owner, source="script")
            else:
                self.issue([Order("attack_group", [u.tag for u in members], meta={"group": target})], owner,
                           source="script")
        elif n in ("move", "retreat") and target:
            p = self._loc(target)
            if p is not None:
                self.issue([Order("move", [u.tag for u in members], point=p)], owner, source="script")
        elif n == "hold":
            self.issue([Order("stop", [u.tag for u in members])], owner, source="script")
        elif n in ("set_mode", "cast") and len(call.args) > 1 and isinstance(call.args[1], StringExpr):
            mode = call.args[1].value
            ability = {"unsieged": "Unsiege", "sieged": "SiegeMode"}.get(mode.lower(), mode)
            self.issue([Order("ability", [u.tag for u in members], meta={"ability": ability})], owner,
                       source="script")
        else:
            self.notes.add(f"script action {n}(...) is not simulated")
            return [f"{text} (not simulated)"]
        return [text]

    def _loc(self, name: str) -> Optional[tuple[float, float]]:
        if name in self.regions:
            r = self.regions[name]
            return (r.x, r.y)
        c = self.centroid(name)
        if c is not None:
            return c
        f = self.sc.forces.get(name)
        return f.spawn if f else None

    # ================================================== World (worldguards)
    def _members(self, name: str) -> list[SimUnit]:
        return [u for u in self.units if u.alive and u.force == name]

    def count(self, name: str) -> Optional[int]:
        if name not in self.sc.forces:
            return None
        return len(self._members(name))

    def centroid(self, name: str) -> Optional[tuple[float, float]]:
        m = self._members(name)
        if not m:
            return None
        return (sum(u.x for u in m) / len(m), sum(u.y for u in m) / len(m))

    def count_in(self, name: str, region: str) -> Optional[int]:
        if name not in self.sc.forces or region not in self.regions:
            return None
        return sum(1 for u in self._members(name) if region in self._regions_of(u))

    def targeting(self, a: str, b: str) -> Optional[bool]:
        m = self._members(a)
        if not m:
            return False
        targets = {u.tag for u in self._members(b)}
        loc = self._loc(b)
        hits = 0
        for u in m:
            o = u.order
            if o is None:
                continue
            if o.kind == "attack_group" and o.group == b:
                hits += 1
            elif o.kind == "attack_unit" and o.target_tag in targets:
                hits += 1
            elif o.kind in ("attack_pt", "move") and loc is not None and o.point is not None \
                    and math.hypot(o.point[0] - loc[0], o.point[1] - loc[1]) < 4:
                hits += 1
        return hits * 2 > len(m)

    def killed_in(self, force: str, region: str) -> Optional[int]:
        return self.kills_in.get((force, region), 0)

    def seconds(self) -> float:
        return self.loop / LOOPS_PER_SECOND

    def elapsed(self, phase: str) -> Optional[float]:
        e = self.entered_at.get(phase)
        return None if e is None else (self.loop - e) / LOOPS_PER_SECOND

    # ============================================================== frames
    def visible_tags(self, player: int) -> set[int]:
        own = [u for u in self.units if u.alive and u.owner == player]
        out = {u.tag for u in own}
        for v in self.units:
            if v.owner == player or not v.alive:
                continue
            if v.burrowed:
                continue
            if any(math.hypot(u.x - v.x, u.y - v.y) <= u.stats.sight + v.radius for u in own):
                out.add(v.tag)
        return out

    def _frame(self) -> Frame:
        tags = self.visible_tags(self.player_id) if self.fog else {u.tag for u in self.units if u.alive}
        units = [Unit(u.tag, u.unit_type, u.owner, u.x, u.y, max(0.0, u.hp), max(0.0, u.shield),
                      max(0.0, u.hp) / u.stats.hp if u.stats.hp else 1.0, structure=u.structure)
                 for u in self.units if u.alive and u.tag in tags]
        f = Frame(self.loop, units, self.player_id)
        res = self.result()
        if res is not None:
            f.done, f.result = True, res
        return f

    def summary(self) -> dict:
        return {"loop": self.loop, "result": self.result(), "marking": self.game.marked(self.state),
                "forces": {n: self.count(n) for n in self.sc.forces}, "notes": sorted(self.notes)}
