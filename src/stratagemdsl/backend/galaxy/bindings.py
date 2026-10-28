"""World bindings -> concrete spawn, region and point descriptions for Galaxy."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from stratagemdsl.core.model import (
    Strategy, EntityDecl, Binding, BindingCall,
)
from stratagemdsl.backend.galaxy.errors import LoweringError


DEFAULT_FILTER = (
    "UnitFilter(0, 0, (1 << c_targetFilterMissile), "
    "(1 << (c_targetFilterDead - 32)) | (1 << (c_targetFilterHidden - 32)))"
)


def _safe(name: str) -> str:
    return ''.join(ch if ch.isalnum() or ch == '_' else '_' for ch in name)


def _str_value(v: Any) -> str:
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, float) and v.is_integer():
        return str(int(v))
    if isinstance(v, (int, float)):
        return str(v)
    return str(v)


def _num(v: float) -> str:
    f = float(v)
    if f.is_integer():
        return str(int(f))
    s = repr(f)
    if "e" in s or "E" in s:
        from decimal import Decimal
        s = format(Decimal(s), "f")
    return s


@dataclass(frozen=True)
class PointRef:
    """A reference to a Galaxy `point` value, either:
      - kind="id":  an existing point_id(N) already placed as an Object on
                    whatever base map this gets packed into (PointFromId(N)
                    at runtime; nothing new is added to PlacedObjects.xml,
                    so N must already exist there or this fails at runtime
                    with "Could not get 'inPos' from parameter in
                    'sUnitCreate'" -- exactly the class of bug that led to
                    this type existing).
      - kind="xy":  raw world coordinates via point_xy(x, y). Lowers to
                    Galaxy's native `Point(x, y)`, which the compiler adapter's
                    codegen (code_gen.py: _create_point/generate_obj) turns
                    into a brand-new synthesized <ObjectPoint> entry in
                    PlacedObjects.xml automatically -- so it works on ANY
                    base map, with no dependency on IDs that happen to
                    already be placed there.
    """
    kind: str  # "id" | "xy" | "expr" (v0.4 derived point)
    id: Optional[int] = None
    x: Optional[float] = None
    y: Optional[float] = None
    text: Optional[str] = None

    def _poll_period(self) -> float:
        setup = self.r.bindings.get("__setup__")
        value = self.r.named(setup.value, "poll_period", 1.0) if setup and isinstance(setup.value, BindingCall) else 1.0
        return self.r._require_positive_number(value, "poll_period")

    def emit(self) -> str:
        if self.kind == "id":
            return f"PointFromId({self.id})"
        if self.kind == "expr":
            return self.text
        return f"Point({_num(self.x)}, {_num(self.y)})"


@dataclass
class SpawnComponent:
    owner: int
    unit_type: str
    count: int
    point: PointRef
    create_flag: str = "0"
    # v0.4: explicit facing in degrees (None keeps the default-facing spawn).
    facing: Optional[float] = None

    def spawn_lines(self, indent: str, group: str, point: Optional[str] = None) -> list[str]:
        pt = self.point.emit() if point is None else point
        if self.facing is None:
            create = f'libNtve_gf_CreateUnitsWithDefaultFacing({self.count}, "{self.unit_type}", {self.create_flag}, {self.owner}, {pt});'
        else:
            create = f'UnitCreate({self.count}, "{self.unit_type}", {self.create_flag}, {self.owner}, {pt}, {float(self.facing)!r});'
        return [indent + create, indent + f"UnitGroupAddUnitGroup({group}, UnitLastCreatedGroup());"]


@dataclass
class BoundEntity:
    decl: EntityDecl
    binding: Binding
    global_name: str
    owner: Optional[int] = None
    spawn_components: list[SpawnComponent] = field(default_factory=list)
    region_center: Optional[PointRef] = None
    region_radius: Optional[float] = None
    dynamic_owner: Optional[int] = None
    dynamic_unit_type: Optional[str] = None
    hallucinated: bool = False
    adopt_types: list[str] = field(default_factory=list)
    region_kind: str = "circle"
    region_rect: Optional[tuple] = None
    region_parts: list = field(default_factory=list)
    attached_to: Optional[str] = None

    @property
    def side(self) -> str:
        return str(self.decl.properties.get("side", ""))


@dataclass(frozen=True)
class CounterSpec:
    force: str
    region: str
    global_name: str
    trigger_name: str
    seen_global: Optional[str] = None


class BindingResolver:
    def __init__(self, strategy: Strategy):
        self.s = strategy
        self.bindings = {b.name: b for b in strategy.bindings}
        self.entities = {e.name: e for e in strategy.world}

    @staticmethod
    def named(call: BindingCall, name: str, default: Any = None) -> Any:
        for a in call.args:
            if a.name == name:
                return a.value
        return default

    @staticmethod
    def positional(call: BindingCall) -> list[Any]:
        return [a.value for a in call.args if a.name is None]

    @staticmethod
    def expect_call(v: Any, *names: str) -> BindingCall:
        if not isinstance(v, BindingCall) or (names and v.name not in names):
            wanted = " or ".join(names) if names else "constructor call"
            raise LoweringError(f"expected {wanted}, got {v!r}")
        return v

    def _require_int(self, val: Any, desc: str, *, min_value: Optional[int] = None) -> int:
        if not isinstance(val, (int, float)) or isinstance(val, bool):
            raise LoweringError(f"{desc} must be a number, got {val!r}")
        f = float(val)
        if not f.is_integer():
            raise LoweringError(f"{desc} must be a whole number, got {val!r} -- silently truncating it would "
                                 f"quietly change owner/army-size/anchor data in a generated experiment")
        n = int(f)
        if min_value is not None and n < min_value:
            raise LoweringError(f"{desc} must be >= {min_value}, got {n}")
        return n

    def _require_positive_number(self, val: Any, desc: str) -> float:
        if not isinstance(val, (int, float)) or isinstance(val, bool):
            raise LoweringError(f"{desc} must be a number, got {val!r}")
        f = float(val)
        if not (f > 0):
            raise LoweringError(f"{desc} must be a positive number, got {val!r}")
        return f

    _DERIVED_POINTS = {"start_location", "offset", "toward", "between", "midpoint", "polar"}

    def _arg(self, call: BindingCall, name: str, idx: int, default: Any = None) -> Any:
        v = self.named(call, name)
        if v is not None:
            return v
        pos = self.positional(call)
        return pos[idx] if idx < len(pos) else default

    def _number(self, val: Any, desc: str) -> float:
        if isinstance(val, bool) or not isinstance(val, (int, float)):
            raise LoweringError(f"{desc} must be a number, got {val!r}")
        return float(val)

    def _derived_point(self, call: BindingCall) -> PointRef:
        """v0.4: points computed from map points / start locations."""
        n = call.name
        if n == "start_location":
            who = self._arg(call, "side", 0)
            player = {"ally": 1, "enemy": 2}.get(who) if isinstance(who, str) else who
            if not isinstance(player, (int, float)) or isinstance(player, bool):
                raise LoweringError(f"start_location(...) expects \"ally\"/\"enemy\" or a player number, got {who!r}")
            return PointRef(kind="expr", text=f"PlayerStartLocation({self._require_int(player, 'start_location player', min_value=1)})")
        a = self.point_ref(self._arg(call, "a", 0)).emit()
        if n == "offset":
            dx, dy = self._number(self._arg(call, "dx", 1), "offset dx"), self._number(self._arg(call, "dy", 2), "offset dy")
            return PointRef(kind="expr", text=f"PointWithOffset({a}, {dx!r}, {dy!r})")
        if n == "polar":
            deg, d = self._number(self._arg(call, "angle", 1), "polar angle"), self._number(self._arg(call, "distance", 2), "polar distance")
            return PointRef(kind="expr", text=f"PointWithOffsetPolar({a}, {d!r}, {deg!r})")
        b = self.point_ref(self._arg(call, "b", 1)).emit()
        if n == "midpoint":
            return PointRef(kind="expr", text=f"MidPoint({a}, {b})")
        if n == "toward":
            d = self._number(self._arg(call, "distance", 2), "toward distance")
            return PointRef(kind="expr", text=f"libNtve_gf_PointOffsetTowardsPoint({a}, {d!r}, {b})")
        t = self._number(self._arg(call, "t", 2), "between t")
        if not 0.0 <= t <= 1.0:
            raise LoweringError("between(a, b, t) needs 0 <= t <= 1")
        return PointRef(kind="expr", text=f"PointInterpolate({a}, {b}, {t!r})")

    def point_ref(self, v: Any) -> PointRef:
        if isinstance(v, BindingCall) and v.name in self._DERIVED_POINTS:
            return self._derived_point(v)
        call = self.expect_call(v, "point_id", "point_xy")
        pos = self.positional(call)
        if call.name == "point_id":
            # Accept both point_id(N) (positional, the corpus convention)
            # and point_id(id=N) (named, matching every other binding call's
            # style, e.g. circle(center=..., radius=...)) -- an LLM that
            # follows the DSL's dominant named-argument convention for a
            # binding call is not "wrong", the parser was just too rigid.
            val = self.named(call, "id")
            if val is None and len(pos) == 1:
                val = pos[0]
            if not isinstance(val, (int, float)):
                raise LoweringError(f"point_id(...) expects one numeric id (positional or id=...), got {v!r}")
            return PointRef(kind="id", id=self._require_int(val, "point_id(...)"))
        else:  # point_xy
            x = self.named(call, "x")
            y = self.named(call, "y")
            if x is None and y is None and len(pos) == 2:
                x, y = pos[0], pos[1]
            if not isinstance(x, (int, float)) or not isinstance(y, (int, float)):
                raise LoweringError(
                    f"point_xy(...) expects two numeric coordinates, either positional point_xy(x, y) "
                    f"or named point_xy(x=.., y=..), got {v!r}"
                )
            return PointRef(kind="xy", x=float(x), y=float(y))

    def _facing(self, v: Any, name: str) -> Optional[float]:
        if v is None:
            return None
        return self._number(v, f"'{name}' facing")

    def _rect(self, call: BindingCall, name: str) -> tuple:
        vals = [self._arg(call, k, i) for i, k in enumerate(("x1", "y1", "x2", "y2"))]
        nums = tuple(self._number(v, f"region '{name}' rect coordinate") for v in vals)
        if not (nums[0] < nums[2] and nums[1] < nums[3]):
            raise LoweringError(f"region '{name}': rect(x1, y1, x2, y2) needs x1 < x2 and y1 < y2")
        return nums

    def _bind_region(self, name: str, call: BindingCall, out: BoundEntity) -> None:
        if call.name == "circle":
            attached = self.named(call, "attached")
            out.region_radius = self._require_positive_number(self.named(call, "radius"), f"region '{name}' radius")
            if attached is not None:
                if not isinstance(attached, str) or attached not in self.entities or self.entities[attached].kind not in {"force", "asset"}:
                    raise LoweringError(f"region '{name}': attached= must name a force/asset")
                out.region_kind = "attached"
                out.attached_to = attached
                return
            out.region_center = self.point_ref(self.named(call, "center"))
        elif call.name == "rect":
            out.region_kind = "rect"
            out.region_rect = self._rect(call, name)
        elif call.name == "union":
            out.region_kind = "union"
            parts = self.positional(call)
            if not parts:
                raise LoweringError(f"region '{name}': union(...) needs at least one circle(...)/rect(...)")
            for part in parts:
                pc = self.expect_call(part, "circle", "rect")
                if pc.name == "rect":
                    out.region_parts.append(("rect", self._rect(pc, name)))
                else:
                    if self.named(pc, "attached") is not None:
                        raise LoweringError(f"region '{name}': union parts cannot be attached")
                    out.region_parts.append(("circle", self.point_ref(self.named(pc, "center")),
                                             self._require_positive_number(self.named(pc, "radius"), f"region '{name}' radius")))
        elif call.name == "whole_map":
            out.region_kind = "whole_map"
        else:
            raise LoweringError(
                f"region '{name}' supports circle(center=..., radius=...), circle(attached=F, radius=...), "
                f"rect(x1, y1, x2, y2), union(...) and whole_map()"
            )

    def bind_entity(self, decl: EntityDecl) -> BoundEntity:
        b = self.bindings.get(decl.name)
        if b is None:
            raise LoweringError(f"missing binding for world entity '{decl.name}'")
        if not isinstance(b.value, BindingCall):
            raise LoweringError(f"binding for '{decl.name}' must be a constructor call")

        gv = f"gv_{_safe(decl.name)}"
        out = BoundEntity(decl=decl, binding=b, global_name=gv)
        call = b.value

        if decl.kind in {"force", "asset"}:
            if call.name not in {"unit_group", "unit", "structure", "group_slice", "dynamic_group", "dynamic_unit"}:
                raise LoweringError(
                    f"{decl.kind} '{decl.name}' cannot lower binding constructor '{call.name}'"
                )
            owner = self.named(call, "owner")
            if owner in {"ally", "Ally"}: owner = 1
            if owner in {"enemy", "Enemy"}: owner = 2
            if not isinstance(owner, (int, float)):
                raise LoweringError(f"'{decl.name}' binding requires owner=1/2")
            owner = self._require_int(owner, f"'{decl.name}' owner", min_value=1)
            out.owner = owner

            # Dynamic bindings query live SC2 units and do not spawn anything themselves.
            if call.name in {"dynamic_group", "dynamic_unit"}:
                out.dynamic_owner = owner
                ut = self.named(call, "unit_type")
                out.dynamic_unit_type = ut if isinstance(ut, str) else None
                hallucinated = self.named(call, "hallucinated", False)
                if not isinstance(hallucinated, bool):
                    raise LoweringError("hallucinated must be a Boolean")
                out.hallucinated = hallucinated
                return out

            loc = (
                self.named(call, "spawn")
                or self.named(call, "at")
                or self.named(call, "source")
            )
            if loc is None:
                raise LoweringError(f"'{decl.name}' binding needs spawn=/at=/source=point_id(...) or point_xy(x, y)")
            pref = self.point_ref(loc)
            # Binding arguments describe the concrete spawn. A world-level
            # default still applies when an individual binding omits the flag.
            construction = self.named(call, "under_construction", decl.properties.get("under_construction", False))
            if not isinstance(construction, bool):
                raise LoweringError(f"'{decl.name}' under_construction must be a Boolean")
            create_flag = "c_unitCreateConstruct" if construction else "0"

            adopt = self.named(call, "adopt", [])
            if not isinstance(adopt, list) or any(not isinstance(x, str) for x in adopt):
                raise LoweringError(f"'{decl.name}' adopt must be a list of unit-type strings")
            out.adopt_types = list(adopt)
            group_facing = self.named(call, "facing")
            comp = self.named(call, "composition")
            if isinstance(comp, list):
                for item in comp:
                    uc = self.expect_call(item, "unit")
                    ut = self.named(uc, "unit_type")
                    cnt = self.named(uc, "count", 1)
                    item_loc = self.named(uc, "spawn") or self.named(uc, "at")
                    item_pref = self.point_ref(item_loc) if item_loc is not None else pref
                    item_flag = "c_unitCreateConstruct" if bool(self.named(uc, "under_construction", False)) else create_flag
                    if not isinstance(ut, str):
                        raise LoweringError(f"bad composition item in '{decl.name}'")
                    cnt_int = self._require_int(cnt, f"composition item count in '{decl.name}'", min_value=1)
                    item_facing = self.named(uc, "facing", group_facing)
                    out.spawn_components.append(SpawnComponent(owner, ut, cnt_int, item_pref, item_flag,
                                                               self._facing(item_facing, decl.name)))
            else:
                ut = self.named(call, "unit_type")
                cnt = self.named(call, "count", 1)
                if not isinstance(ut, str):
                    raise LoweringError(f"'{decl.name}' binding needs unit_type=\"...\"")
                cnt_int = self._require_int(cnt, f"'{decl.name}' count", min_value=1)
                out.spawn_components.append(SpawnComponent(owner, ut, cnt_int, pref, create_flag,
                                                           self._facing(group_facing, decl.name)))

        elif decl.kind == "region":
            self._bind_region(decl.name, call, out)

        elif decl.kind == "route":
            # Route is preserved in the strategic model. Current Galaxy backend needs a concrete
            # target point before a Move/Retreat can be emitted.
            if call.name != "route":
                raise LoweringError(f"route '{decl.name}' requires route(...) binding")
        else:
            raise LoweringError(f"unsupported world kind: {decl.kind}")

        return out


