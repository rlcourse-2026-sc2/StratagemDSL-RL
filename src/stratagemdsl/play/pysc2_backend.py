"""The real game through PySC2's raw interface.

PySC2 and a StarCraft II installation are optional dependencies, imported only
when this backend is built (`pip install pysc2`; SC2PATH pointing at the game).

Frames: PySC2's raw coordinates put the origin top-left and floor positions to
cells (`features._world_to_minimap_px`: y flipped about the map height, scaled
by raw_resolution / max map side, then floored). We request raw_resolution =
the larger map side, so the scale is 1 and

    world -> raw   (x, H - y)            raw -> world   (rx + 0.5, H - ry - 0.5)

where H is the map height from the game itself. The tracker's calibration
check (units first seen near their spawn points) catches a mismatch.

Players: player 1 is the agent; player 2 is a built-in bot at the given
difficulty. The map's trigger script commands the enemy forces; a melee AI
may still give its own orders, so prefer `very_easy` and check the logs.
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from stratagemdsl.play.game import Frame, Order, Unit
from stratagemdsl.play.scenario import Scenario
from stratagemdsl.views.routes import FOOTPRINT

RESULT = {1: "victory", -1: "defeat", 0: "tie"}


def raw_to_world(rx: float, ry: float, height: float) -> tuple[float, float]:
    """A raw unit position (floored cell, origin top-left) -> the centre of that cell in world coordinates."""
    return (float(rx) + 0.5, height - float(ry) - 0.5)


def world_to_raw(x: float, y: float, height: float) -> tuple[float, float]:
    """A world point -> the raw point PySC2 turns back into (floor(x) + 0.5, height - floor(height - y) - 0.5)."""
    return (x, height - y)


class PySC2Backend:
    def __init__(self, map_path: str | Path, scenario: Scenario, *, step_mul: int = 8, max_loops: int = 22 * 60 * 15,
                 bot_difficulty: str = "very_easy", realtime: bool = False, visualize: bool = False,
                 sc2_version: Optional[str] = None, disable_fog: bool = False, seed: Optional[int] = None,
                 replay_dir: Optional[str] = None):
        try:
            from pysc2.env import sc2_env
            from pysc2.lib import actions, features, units
            from pysc2.maps import lib as maps_lib
        except ImportError as e:  # pragma: no cover - depends on the installation
            raise RuntimeError("PySC2 is not installed: pip install pysc2 (and set SC2PATH)") from e
        self._actions, self._units = actions, units
        self.sc = scenario
        map_path = Path(map_path).resolve()
        if not map_path.is_file():
            raise FileNotFoundError(map_path)

        # A Map subclass per map file; its own class name keeps PySC2's map
        # registry free of duplicates when several backends live in one process.
        map_cls = type(f"StratagemMap_{abs(hash(str(map_path))):x}", (maps_lib.Map,), dict(
            directory=str(map_path.parent),     # absolute: run_config.map_data joins it unchanged
            filename=map_path.stem, players=2, game_steps_per_episode=max_loops, step_mul=step_mul,
            score_index=-1))                    # reward = win/loss
        self._map = map_cls()
        side = max(scenario.profile.width, scenario.profile.height)
        race = {"protoss": sc2_env.Race.protoss, "terran": sc2_env.Race.terran, "zerg": sc2_env.Race.zerg,
                "random": sc2_env.Race.random}
        self.env = sc2_env.SC2Env(
            map_name=self._map,
            players=[sc2_env.Agent(race[scenario.race("ally")]),
                     sc2_env.Bot(race[scenario.race("enemy")], sc2_env.Difficulty[bot_difficulty])],
            agent_interface_format=features.AgentInterfaceFormat(
                action_space=actions.ActionSpace.RAW, use_raw_units=True, raw_resolution=side),
            step_mul=step_mul, game_steps_per_episode=max_loops, realtime=realtime, visualize=visualize,
            score_index=-1, disable_fog=disable_fog, ensure_available_actions=False, version=sc2_version,
            random_seed=seed, save_replay_episodes=1 if replay_dir else 0, replay_dir=replay_dir)
        self.height = float(scenario.profile.height)
        self.max_loops = max_loops

    # -------------------------------------------------------------- frames
    def _map_height(self) -> float:
        try:  # the game's own map size, when the environment exposes it
            return float(self.env._game_info[0].start_raw.map_size.y)
        except Exception:
            return self.height

    def _frame(self, ts) -> Frame:
        obs = ts.observation
        H = self._map_height()
        out = []
        for u in obs.raw_units:
            try:
                name = self._units.get_unit_type(int(u.unit_type)).name
            except Exception:
                name = str(int(u.unit_type))
            x, y = raw_to_world(u.x, u.y, H)
            out.append(Unit(int(u.tag), name, int(u.owner), x, y,
                            float(u.health), float(u.shield), float(u.health_ratio) / 255.0,
                            structure=name in FOOTPRINT))
        frame = Frame(int(obs.game_loop[0]), out, int(obs.player.player_id))
        if ts.last():
            frame.done = True
            frame.result = RESULT.get(int(ts.reward), "tie")
            if frame.result == "tie" and frame.game_loop >= self.max_loops - 16:
                frame.result = "timeout"
        return frame

    def _raw_point(self, p: tuple[float, float]) -> tuple[float, float]:
        return world_to_raw(p[0], p[1], self._map_height())

    def _to_actions(self, orders: list[Order]):
        F = self._actions.RAW_FUNCTIONS
        out = []
        for o in orders:
            if not o.tags:
                continue
            if o.kind == "hold":
                out.append(F.HoldPosition_quick("now", o.tags))
            elif o.kind == "move":
                out.append(F.Move_pt("now", o.tags, self._raw_point(o.point)))
            elif o.kind == "attack_pt":
                out.append(F.Attack_pt("now", o.tags, self._raw_point(o.point)))
            elif o.kind == "attack_unit":
                out.append(F.Attack_unit("now", o.tags, o.target_tag))
        return out or [F.no_op()]

    # ------------------------------------------------------------ backend
    def reset(self) -> Frame:
        return self._frame(self.env.reset()[0])

    def step(self, orders: list[Order]) -> Frame:
        return self._frame(self.env.step([self._to_actions(orders)])[0])

    def close(self) -> None:
        self.env.close()
