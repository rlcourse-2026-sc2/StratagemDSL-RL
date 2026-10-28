"""Episode loop: observe, let the agent decide every N seconds of game time, step, log.

Outputs in the run directory:
    episodes.jsonl        one line per episode: result, duration, LLM calls and tokens, events
    episode_<k>.jsonl     every decision of episode k: state, prompt, reply, orders, errors
    summary.json          win rate with a Wilson 95% interval, means, the run's settings
"""
from __future__ import annotations

import json
import math
import time
from pathlib import Path
from typing import Callable, Optional

from stratagemdsl.play.actions import to_orders
from stratagemdsl.play.agents import Agent
from stratagemdsl.play.game import LOOPS_PER_SECOND, Backend
from stratagemdsl.play.observe import ForceTracker
from stratagemdsl.play.scenario import Scenario


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return (0.0, 1.0)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (round(max(0.0, c - h), 4), round(min(1.0, c + h), 4))


def run_episode(backend: Backend, agent: Agent, scenario: Scenario, *, decision_seconds: float = 4.0,
                log: Optional[Callable[[dict], None]] = None, max_steps: int = 1_000_000) -> dict:
    log = log or (lambda record: None)
    started = time.monotonic()
    frame = backend.reset()
    tracker = ForceTracker(scenario, frame.player_id)
    tracker.update(frame)
    agent.reset(scenario, decision_seconds)
    every = max(1, int(round(decision_seconds * LOOPS_PER_SECOND)))
    next_decision, cursor = frame.game_loop, 0
    stats = {"decisions": 0, "llm_calls": 0, "input_tokens": 0, "output_tokens": 0, "invalid_answers": 0,
             "orders": 0, "llm_seconds": 0.0}
    for _ in range(max_steps):
        orders = []
        if frame.game_loop >= next_decision:
            events, cursor = tracker.events[cursor:], len(tracker.events)
            d = agent.decide(frame, tracker, events)
            orders, notes = to_orders(d.actions, scenario, tracker)
            stats["decisions"] += 1
            stats["orders"] += len(orders)
            stats["llm_calls"] += len(d.calls)
            stats["invalid_answers"] += sum(1 for c in d.calls if c.get("errors"))
            for c in d.calls:
                stats["input_tokens"] += c.get("input_tokens", 0)
                stats["output_tokens"] += c.get("output_tokens", 0)
                stats["llm_seconds"] += c.get("seconds", 0.0)
            log({"type": "decision", "loop": frame.game_loop, "state": tracker.summary(), "events": events,
                 "actions": [a.to_dict() for a in d.actions], "errors": d.errors, "notes": notes,
                 "note": d.note, "calls": d.calls})
            next_decision = frame.game_loop + every
        frame = backend.step(orders)
        tracker.update(frame)
        if frame.done:
            break
    else:
        frame.result = frame.result or "step_limit"
    record = {"result": frame.result, "game_loop": frame.game_loop,
              "game_seconds": round(frame.game_loop / LOOPS_PER_SECOND, 1),
              "wall_seconds": round(time.monotonic() - started, 1), **stats,
              "llm_seconds": round(stats["llm_seconds"], 1),
              "final_state": tracker.summary(), "events": tracker.events,
              "calibration": tracker.calibration, "calibration_warning": tracker.calibration_problem()}
    log({"type": "end", **record})
    return record


def run(make_backend: Callable[[], Backend], agent: Agent, scenario: Scenario, *, episodes: int = 1,
        decision_seconds: float = 4.0, out_dir: Optional[Path] = None, settings: Optional[dict] = None,
        on_episode: Optional[Callable[[int, dict], None]] = None) -> dict:
    out = Path(out_dir) if out_dir else None
    if out:
        out.mkdir(parents=True, exist_ok=True)
    results = []
    backend = make_backend()
    try:
        for k in range(episodes):
            log_file = (out / f"episode_{k}.jsonl").open("w", encoding="utf-8") if out else None
            try:
                def log(rec, f=log_file):
                    if f:
                        f.write(json.dumps(rec, ensure_ascii=False, default=str) + "\n")
                rec = run_episode(backend, agent, scenario, decision_seconds=decision_seconds, log=log)
            finally:
                if log_file:
                    log_file.close()
            rec["episode"] = k
            results.append(rec)
            if out:
                with (out / "episodes.jsonl").open("a", encoding="utf-8") as f:
                    f.write(json.dumps({k2: v for k2, v in rec.items() if k2 != "final_state"},
                                       ensure_ascii=False, default=str) + "\n")
            if on_episode:
                on_episode(k, rec)
    finally:
        backend.close()
    summary = summarize(results)
    summary["agent"] = agent.name
    summary["settings"] = settings or {}
    if out:
        (out / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2, default=str),
                                          encoding="utf-8")
    return summary


def summarize(results: list[dict]) -> dict:
    n = len(results)
    counts: dict[str, int] = {}
    for r in results:
        counts[r["result"]] = counts.get(r["result"], 0) + 1
    wins = counts.get("victory", 0)

    def mean(key):
        vals = [r[key] for r in results if r.get(key) is not None]
        return round(sum(vals) / len(vals), 2) if vals else None
    return {"episodes": n, "results": counts, "win_rate": round(wins / n, 4) if n else None,
            "win_rate_ci95": wilson(wins, n), "mean_game_seconds": mean("game_seconds"),
            "mean_decisions": mean("decisions"), "mean_llm_calls": mean("llm_calls"),
            "mean_input_tokens": mean("input_tokens"), "mean_output_tokens": mean("output_tokens"),
            "invalid_answers": sum(r.get("invalid_answers", 0) for r in results),
            "calibration_warnings": sorted({r["calibration_warning"] for r in results if r.get("calibration_warning")})}
