"""`strat` command line: run the pipeline up to one layer and inspect its output.

    strat parse   FILE            AST summary (or --json)           layer 1
    strat check   FILE            diagnostics (+ --pattern-report)  layer 3
    strat lower   FILE -o DIR     .galaxy, intents, PlanGraph       layer 4
    strat compile FILE -o DIR     + Triggers.xml / PlacedObjects    layer 5
    strat pack    FILE -o DIR     + .SC2Map with readback           layer 6
                                 --oracle also scripts allied orders into that map
                                 --gameover ends the game at a terminal phase (LLM-PySC2 episodes)
    strat net     FILE            Petri-net analysis (--pnml, --cross-check)  layer 3
    strat graph   FILE -o DIR     PlanGraph + Petri net DOT/SVG, Mermaid, JSON, PNML
    strat route   FILE -o DIR     movement legs of the plan as ground paths on the base map
    strat play    FILE --map MAP  LLM / scripted agents play a --gameover map through PySC2
    strat llm-pysc2 FILE -o DIR   --gameover map + task bundle for LLM-PySC2 (llm_pysc2.bin.stratagem_run)
    strat export-api DIR          API catalogue and LLM tool schema
    strat mapinfo MAP             terrain profile of a base map (what the LLM sees)
    strat generate --seed S --base-map MAP ...   LLM variant -> checks -> Galaxy -> XML -> .SC2Map

Exit codes: 0 ok, 1 diagnostics/stage failure, 2 parse failure.
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

from stratagemdsl import paths, pipeline


def _out_dir(args) -> Path:
    return Path(args.out_dir) if args.out_dir else paths.build_dir() / Path(args.source).stem


def cmd_parse(args) -> int:
    try:
        strategy = pipeline.parse(args.source, frontend=args.frontend, check_agreement=not args.no_agreement)
    except Exception as exc:
        print(f"[PARSE ERROR] {exc}")
        return 2
    if args.json:
        text = json.dumps(strategy.to_dict(), ensure_ascii=False, indent=2)
        if args.json == "-":
            print(text)
        else:
            Path(args.json).parent.mkdir(parents=True, exist_ok=True)
            Path(args.json).write_text(text, encoding="utf-8")
            print(f"AST JSON: {args.json}")
        return 0
    print(f"strategy     : {strategy.name}")
    print(f"world        : {len(strategy.world)} entities")
    print(f"plan nodes   : {len(strategy.plan.nodes)}  start={strategy.plan.start}")
    print(f"transitions  : {len(strategy.plan.transitions)}")
    print(f"bindings     : {len(strategy.bindings)}")
    return 0


def cmd_check(args) -> int:
    try:
        strategy = pipeline.parse(args.source, frontend=args.frontend)
    except Exception as exc:
        print(f"[PARSE ERROR] {exc}")
        return 2
    validator = pipeline.validate(strategy, strict=not args.loose)
    bag = validator.diagnostics
    for d in bag.items:
        print(d)
    if not bag.items:
        print("[OK] no diagnostics")
    if args.pattern_report and getattr(validator, "pattern_report", None) is not None:
        from stratagemdsl.semantics.patterns.report import format_pattern_report
        print()
        print(format_pattern_report(validator.pattern_report))
    return 1 if bag.has_errors else 0


def _cmd_until(stage: str):
    def run(args) -> int:
        out = _out_dir(args)
        r = pipeline.run(args.source, until=stage, strict=not args.loose, frontend=args.frontend, out_dir=out,
                         base_map=Path(args.base_map) if getattr(args, "base_map", None) else None,
                         compiler_root=Path(args.compiler_root) if args.compiler_root else None,
                         oracle=getattr(args, "oracle", False), gameover=getattr(args, "gameover", False))
        for d in r.diagnostics:
            print(d)
        for stage_name, status in r.stages.items():
            print(f"{stage_name:8} {status}")
        if r.base_map is not None:
            print(f"base map {r.base_map.name}")
        if r.ok:
            print(f"[OK] artifacts in {out}")
            return 0
        print(f"[FAILED at {r.failed_stage}] {r.error}")
        return 2 if r.failed_stage == "parse" else 1
    return run


def cmd_graph(args) -> int:
    from stratagemdsl.frontend import parse_file
    from stratagemdsl.views.plangraph import write_views
    strategy = parse_file(args.source, args.frontend)
    out = _out_dir(args)
    result = write_views(strategy, out, Path(args.source).stem)
    model = result["model"]
    print(f"lowering ok: {model.lowering_ok} {model.lowering_error}")
    for name in result["files"]:
        print(f"  {out / name}")
    return 0


def cmd_route(args) -> int:
    """Where each force moves, along which ground path (views.routes)."""
    from stratagemdsl.frontend import parse_file
    from stratagemdsl.views.routes import guess_base_map, write_routes
    strategy = parse_file(args.source, args.frontend)
    base = Path(args.base_map) if args.base_map else guess_base_map(Path(args.source), paths.base_maps_dir())
    out = _out_dir(args)
    plan, files = write_routes(strategy, base, out, Path(args.source).stem, png=not args.no_png)
    print(f"map {base.name} ({plan.size[0]} x {plan.size[1]})")
    rows = [("force", "context", "from -> to", "status", "cells", "ramps")]
    for leg in plan.legs:
        rows.append((leg.force, leg.context, f"{leg.origin.replace('spawn:', 'spawn ')} -> {leg.target}",
                     leg.status, f"{leg.length:.1f}" if leg.length else "-", "/".join(leg.ramps) or "-"))
    widths = [max(len(r[i]) for r in rows) for i in range(len(rows[0]))]
    for row in rows:
        print("  ".join(c.ljust(w) for c, w in zip(row, widths)).rstrip())
    for w in plan.warnings:
        print(f"warning: {w}")
    for name in files:
        print(f"  {out / name}")
    bad = [l for l in plan.legs if l.status in ("unreachable", "no_position")]
    return 1 if args.strict and bad else 0


def cmd_play(args) -> int:
    """Play a map built from FILE with an agent; see docs/PLAY.md."""
    from stratagemdsl.frontend import parse_file
    from stratagemdsl.packaging.mpq import open_archive
    from stratagemdsl.packaging.terrain import load_profile
    from stratagemdsl.play import agents, runner
    from stratagemdsl.play.scenario import build_scenario

    strategy = parse_file(args.source, args.frontend)
    map_path = Path(args.map)
    profile = load_profile(map_path)
    scenario = build_scenario(strategy, profile)
    if not scenario.controlled:
        print("this strategy has no allied force to command")
        return 1
    if not args.dry_run:
        with open_archive(map_path) as archive:
            script = archive.read("MapScript.galaxy").decode("utf-8", "replace")
        if "GameOver(" not in script and not args.allow_no_gameover:
            print(f"{map_path.name} never calls GameOver, so an episode would only end at the time limit; "
                  "build it with `strat pack ... --gameover` (or pass --allow-no-gameover)")
            return 1

    decision_seconds = args.decision_seconds
    if args.agent in ("llm", "intents"):
        from stratagemdsl.play.llm import ProviderDecider, ScriptedDecider
        if args.provider or not args.dry_run:
            from stratagemdsl.llm.config import resolve_provider
            decider = ProviderDecider(resolve_provider(args.provider, args.model, args.api_key, args.base_url,
                                                       Path(args.config) if args.config else None),
                                      max_tokens=args.max_tokens)
        else:
            answers = Path(args.answers).read_text(encoding="utf-8").splitlines() if args.answers else []
            decider = ScriptedDecider([a for a in answers if a.strip()] or ['{"orders": [], "note": "dry run"}'])
        agent = agents.LLMAgent(decider, with_plan=args.agent == "intents", terrain_grid=args.terrain_grid)
        model = decider.model
    elif args.agent == "direct":
        agent = agents.ScriptedAgent(args.orders or agents.default_direct_orders(scenario))
        model = None
    else:
        agent = agents.IdleAgent()
        model = None

    max_loops = int(args.max_minutes * 60 * 22.4)
    if args.dry_run and args.sim == "plan":
        from stratagemdsl.play.plansim import PlanSim
        def make_backend():
            return PlanSim(strategy, profile, scenario=scenario, max_loops=max_loops, seed=args.seed,
                           oracle=args.agent == "plan")
    elif args.dry_run:
        from stratagemdsl.play.toysim import ToySim
        def make_backend():
            return ToySim(scenario, max_loops=max_loops)
    else:
        from stratagemdsl.play.pysc2_backend import PySC2Backend
        def make_backend():
            return PySC2Backend(map_path, scenario, step_mul=args.step_mul, max_loops=max_loops,
                                bot_difficulty=args.bot, sc2_version=args.sc2_version, seed=args.seed,
                                replay_dir=str(Path(args.replays).resolve()) if args.replays else None,
                                visualize=args.visualize)
    out = Path(args.out_dir) if args.out_dir else paths.build_dir() / "play" / f"{Path(args.source).stem}_{agent.name}"
    settings = {"source": str(args.source), "map": str(map_path), "agent": agent.name, "model": model,
                "episodes": args.episodes, "decision_seconds": decision_seconds, "max_minutes": args.max_minutes,
                "step_mul": args.step_mul, "bot": args.bot, "dry_run": args.dry_run, "orders": args.orders}

    def progress(k, rec):
        print(f"episode {k + 1}/{args.episodes}: {rec['result']} at {rec['game_seconds']:.0f} s game time, "
              f"{rec['decisions']} decisions, {rec['llm_calls']} LLM calls"
              + (f"  [warning: {rec['calibration_warning']}]" if rec.get("calibration_warning") else ""), flush=True)
    summary = runner.run(make_backend, agent, scenario, episodes=args.episodes, decision_seconds=decision_seconds,
                         out_dir=out, settings=settings, on_episode=progress)
    lo, hi = summary["win_rate_ci95"]
    print(f"{agent.name}: win rate {summary['win_rate']:.2f} (95% CI {lo:.2f}-{hi:.2f}) over {summary['episodes']} "
          f"episodes; results {summary['results']}")
    print(f"logs in {out}")
    return 0


def cmd_llm_pysc2(args) -> int:
    """Build a --gameover map (unless --map is given) and the LLM-PySC2 task bundle next to it."""
    from stratagemdsl.frontend import parse_file
    from stratagemdsl.packaging.terrain import load_profile
    from stratagemdsl.play.llm_pysc2 import build_bundle, write_bundle

    out = _out_dir(args)
    stem = Path(args.source).stem
    if args.map:
        map_path = Path(args.map)
        if not args.base_map:
            print("--map needs --base-map (the terrain the map was built on)")
            return 1
        base = Path(args.base_map)
    else:
        r = pipeline.run(args.source, until="pack", strict=not args.loose, frontend=args.frontend, out_dir=out,
                         base_map=Path(args.base_map) if args.base_map else None,
                         compiler_root=Path(args.compiler_root) if args.compiler_root else None,
                         oracle=args.oracle, gameover=True)
        for d in r.diagnostics:
            print(d)
        for stage_name, status in r.stages.items():
            print(f"{stage_name:8} {status}")
        if not r.ok:
            print(f"[FAILED at {r.failed_stage}] {r.error}")
            return 2 if r.failed_stage == "parse" else 1
        map_path, base = out / f"{stem}.SC2Map", r.base_map
        print(f"base map {base.name}")
    strategy = parse_file(args.source, args.frontend)
    profile = load_profile(base)
    bundle = build_bundle(strategy, profile, map_path, source=Path(args.source), gameover=True, oracle=args.oracle,
                          screen=args.screen, minimap=args.minimap, camera_width=args.camera_width)
    path = write_bundle(bundle, out, stem)
    controlled = [f["name"] for f in bundle["forces"] if f["controlled"]]
    print(f"map     {map_path}")
    print(f"bundle  {path}")
    print(f"races   ally {bundle['races']['ally']} vs enemy {bundle['races']['enemy']}; "
          f"agents for {', '.join(controlled) or '(none)'}")
    print("run it with LLM-PySC2:")
    print(f"  python -m llm_pysc2.bin.stratagem_run --bundle {path} --condition intents --model <name> "
          f"--api-base <url> --api-key <key>")
    print(f"  python -m llm_pysc2.bin.stratagem_run --bundle {path} --engine fake --model offline   # no SC2, no LLM")
    return 0


def cmd_net(args) -> int:
    """Compile the plan to its Petri net and print the analysis."""
    from stratagemdsl.frontend import parse_file
    from stratagemdsl.net import analyze, build_net
    from stratagemdsl.net.pnml import to_pnml
    strategy = parse_file(args.source, args.frontend)
    net = build_net(strategy)
    report = analyze(net)
    summary = report.summary()
    if args.cross_check:
        from stratagemdsl.net.snakes_bridge import cross_check
        cc = cross_check(net)
        summary["snakes_cross_check"] = {"ok": cc.ok, "markings": cc.ours, "snakes_markings": cc.snakes}
    print(json.dumps(summary, ensure_ascii=False, indent=2, default=str))
    if args.pnml:
        Path(args.pnml).parent.mkdir(parents=True, exist_ok=True)
        Path(args.pnml).write_text(to_pnml(net, plain=args.plain), encoding="utf-8")
        print(f"PNML written to {args.pnml}", file=sys.stderr)
    return 0


def cmd_export_api(args) -> int:
    from stratagemdsl.registry.contracts import catalog_json, catalog_markdown
    from stratagemdsl.registry.schema import strategy_json_schema
    out = Path(args.directory)
    out.mkdir(parents=True, exist_ok=True)
    (out / "API_CONTRACTS.md").write_text(catalog_markdown() + "\n", encoding="utf-8")
    # STRATEGY_TOOL.json is the parameter schema of the emit_stratagem_variant tool.
    for name, payload in (("API_CONTRACTS.json", catalog_json()), ("STRATEGY_TOOL.json", strategy_json_schema())):
        (out / name).write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"API catalogue written to {out}")
    return 0


def cmd_mapinfo(args) -> int:
    from stratagemdsl.packaging.terrain import load_profile
    profile = load_profile(args.map)
    text = profile.render_grid() if args.grid_only else profile.render_context()
    if args.output:
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.output).write_text(text + "\n", encoding="utf-8")
        print(f"terrain profile written to {args.output}")
    else:
        print(text)
    if args.check:
        from stratagemdsl.frontend import parse_file
        from stratagemdsl.packaging.terrain import check_bindings
        problems = check_bindings(parse_file(args.check, "lark"), profile)
        for item in problems:
            print(f"[TERRAIN] {item}")
        print("[OK] every point fits this map" if not problems else f"{len(problems)} problem(s)")
        return 1 if problems else 0
    return 0


def _designer_brief(args) -> str:
    lines = [args.brief] if args.brief else []
    params = [p.split("=", 1) for p in args.param]
    bad = [p for p in params if len(p) != 2]
    if bad:
        raise SystemExit(f"--param expects KEY=VALUE, got {bad[0][0]!r}")
    if params:
        lines.append("Designer parameters (all must be honoured):")
        lines += [f"  - {k.strip()}: {v.strip()}" for k, v in params]
    return "\n".join(lines)


def cmd_generate(args) -> int:
    from stratagemdsl.llm.config import resolve_provider
    from stratagemdsl.llm.client import HEARTBEAT_SECONDS
    from stratagemdsl.llm.pipeline import run_llm_variant
    try:
        from stratagemdsl.llm.config import _json_object
        extra = _json_object(args.extra_body, "--extra-body") if args.extra_body else None
        provider = resolve_provider(args.provider, args.model, args.api_key, args.base_url,
                                    Path(args.config) if args.config else None, args.replay,
                                    extra_body=extra, thinking=False if args.no_thinking else None)
    except ValueError as exc:
        print(f"[CONFIG] {exc}")
        return 2
    out = Path(args.out_dir) if args.out_dir else paths.build_dir() / "llm" / Path(args.seed).stem
    brief = _designer_brief(args)
    if args.base_map:
        from stratagemdsl.packaging.terrain import brief_coordinate_problems, load_profile
        profile = load_profile(args.base_map)
        for item in brief_coordinate_problems(brief, profile):
            print(f"[WARN] --brief/--param mention {item}; coordinates must come from "
                  f"`strat mapinfo {args.base_map}`")
    records, failures = [], 0
    for i in range(args.n):
        theme = args.theme if args.n == 1 else f"{args.theme}_{i + 1}"
        print(f"=== variant {i + 1}/{args.n}: provider={provider.key} model={provider.model} theme={theme} ===",
              flush=True)
        if i == 0 and provider.key != "replay":
            print(f"  (one call can take several minutes on thinking models; progress every "
                  f"{int(HEARTBEAT_SECONDS)} s)"
                  + (f"; extra_body={json.dumps(provider.extra_body)}" if provider.extra_body else ""), flush=True)
        record = run_llm_variant(
            provider, args.seed, theme, compiler_root=args.compiler_root or paths.compiler_root(), out_dir=out,
            brief=brief, temperature=args.temperature, max_tokens=args.max_tokens, max_repairs=args.max_repairs,
            use_tool_calling=not args.no_tool_calling, base_map=args.base_map, strict=not args.loose,
        )
        if record.get("ok"):
            print(f"  [OK] {record['name']} -> {record['out_dir']}"
                  + (f" (map {record['map']['status']})" if record.get("map") else ""))
        else:
            failures += 1
            print(f"  [FAILED at {record.get('stage')}] {str(record.get('error', ''))[:300]}")
        records.append(record)
    out.mkdir(parents=True, exist_ok=True)
    (out / "generation_records.json").write_text(json.dumps(records, ensure_ascii=False, indent=2, default=str),
                                                 encoding="utf-8")
    print(f"records: {out / 'generation_records.json'}")
    return 1 if failures else 0


def build_parser() -> argparse.ArgumentParser:
    import stratagemdsl
    ap = argparse.ArgumentParser(prog="strat", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("-V", "--version", action="version", version=f"strat (StratagemDSL) {stratagemdsl.__version__}")
    sub = ap.add_subparsers(dest="command", required=True)

    def source_cmd(name, func, help_, *, outputs=False):
        p = sub.add_parser(name, help=help_)
        p.add_argument("source", help=".strat file")
        p.add_argument("--frontend", choices=["lark", "antlr", "auto"], default="lark")
        if outputs:
            p.add_argument("-o", "--out-dir", help="artifact directory (default build/<stem>)")
            p.add_argument("--loose", action="store_true", help="skip strict SC2 executability rules")
            p.add_argument("--oracle", action="store_true",
                           help="also emit allied attack/move/cast orders into Galaxy and the map")
            p.add_argument("--gameover", action="store_true",
                           help="end the game with GameOver at a terminal phase (one game = one scored "
                                "episode, for LLM agents through PySC2; leave off for MARL training maps)")
            p.add_argument("--compiler-root", help="galaxycc root (default vendor/galaxy_compiler)")
        p.set_defaults(func=func)
        return p

    p = source_cmd("parse", cmd_parse, "parse and summarise the AST")
    p.add_argument("--json", metavar="FILE", help="write the AST as JSON ('-' for stdout)")
    p.add_argument("--no-agreement", action="store_true", help="do not cross-check the other frontend")
    p = source_cmd("check", cmd_check, "run semantic checks")
    p.add_argument("--loose", action="store_true", help="skip strict SC2 executability rules")
    p.add_argument("--pattern-report", action="store_true", help="print the strategic pattern proof")
    source_cmd("lower", _cmd_until("lower"), "lower to Galaxy", outputs=True)
    source_cmd("compile", _cmd_until("compile"), "compile Galaxy to trigger XML", outputs=True)
    p = source_cmd("pack", _cmd_until("pack"), "pack an .SC2Map and read it back", outputs=True)
    p.add_argument("--base-map", help="base .SC2Map (default: guessed from the file name, e.g. cerulean_* -> "
                                      "cerulean_fall_le, arid_* -> arid_plateau, sdjx_* -> sdjx_te; else jctq_te)")
    p = source_cmd("graph", cmd_graph, "export the PlanGraph / Petri net views")
    p.add_argument("-o", "--out-dir")
    p = source_cmd("route", cmd_route, "plot the plan's movement legs as ground paths on the base map")
    p.add_argument("-o", "--out-dir")
    p.add_argument("--base-map", help="base .SC2Map (default: guessed from the file name, e.g. cerulean_* -> "
                                      "cerulean_fall_le, sdjx_* -> sdjx_te)")
    p.add_argument("--no-png", action="store_true", help="skip the matplotlib PNG (JSON and SVG are always written)")
    p.add_argument("--strict", action="store_true", help="exit 1 if a leg is unreachable or has no coordinates")
    p = source_cmd("play", cmd_play, "play a --gameover map with an LLM or scripted agent through PySC2")
    p.add_argument("--map", required=True, help="the .SC2Map built from this file (strat pack --gameover)")
    p.add_argument("--agent", choices=["llm", "intents", "plan", "direct"], default="llm",
                   help="llm: objective only; intents: plus the plan; plan: no agent (use an --oracle map); "
                        "direct: fixed orders, no stratagem")
    p.add_argument("--orders", nargs="*", help="direct agent: force:action[:target] ... (default: every "
                                                 "allied force attacks the largest enemy force)")
    p.add_argument("--episodes", type=int, default=1)
    p.add_argument("--decision-seconds", type=float, default=4.0, help="game seconds between LLM decisions")
    p.add_argument("--max-minutes", type=float, default=15.0, help="game-time limit per episode")
    p.add_argument("--step-mul", type=int, default=8)
    p.add_argument("--bot", default="very_easy", help="difficulty of PySC2's built-in player 2")
    p.add_argument("--sc2-version", help="SC2 build PySC2 should start (e.g. 4.10)")
    p.add_argument("--seed", type=int)
    p.add_argument("--replays", help="save one replay per episode into this directory")
    p.add_argument("--visualize", action="store_true", help="PySC2's pygame viewer")
    p.add_argument("--allow-no-gameover", action="store_true")
    p.add_argument("--dry-run", action="store_true",
                   help="toy movement simulator instead of SC2 (no game needed); scripted answers unless --provider")
    p.add_argument("--answers", help="dry run: a file with one JSON answer per line")
    p.add_argument("--sim", choices=["toy", "plan"], default="toy",
                   help="dry run: toy = movement only; plan = the plan's Petri net scripts the enemy, toy combat "
                        "and ground paths (play.plansim); with --agent plan the plan also commands allies")
    p.add_argument("--terrain-grid", action="store_true", help="include the full terrain grid in the prompt")
    p.add_argument("--provider")
    p.add_argument("--model")
    p.add_argument("--api-key")
    p.add_argument("--base-url")
    p.add_argument("--config", help="JSON provider config (default ~/.stratagemdsl/llm.json)")
    p.add_argument("--max-tokens", type=int, default=4096)
    p.add_argument("-o", "--out-dir")
    p = source_cmd("llm-pysc2", cmd_llm_pysc2, "build a --gameover map and the LLM-PySC2 task bundle")
    p.add_argument("-o", "--out-dir", help="artifact directory (default build/<stem>)")
    p.add_argument("--base-map", help="base .SC2Map (default: guessed from the file name, like pack)")
    p.add_argument("--map", help="use this already built --gameover map instead of packing (needs --base-map)")
    p.add_argument("--oracle", action="store_true", help="the map also scripts allied orders (plan baseline)")
    p.add_argument("--loose", action="store_true", help="skip strict SC2 executability rules")
    p.add_argument("--compiler-root", help="galaxycc root (default vendor/galaxy_compiler)")
    p.add_argument("--screen", type=int, default=128, help="feature screen size LLM-PySC2 will use")
    p.add_argument("--minimap", type=int, default=64, help="feature minimap size LLM-PySC2 will use")
    p.add_argument("--camera-width", type=int, default=24, help="camera width in world cells")
    p = source_cmd("net", cmd_net, "print the plan's Petri net analysis")
    p.add_argument("--pnml", metavar="FILE", help="also write the net as PNML")
    p.add_argument("--plain", action="store_true", help="PNML of the plain P/T expansion (once/halting/capacity as places)")
    p.add_argument("--cross-check", action="store_true", help="compare the token rules with SNAKES (pip install snakes)")
    p = sub.add_parser("export-api", help="write API_CONTRACTS.md/.json and STRATEGY_TOOL.json")
    p.add_argument("directory")
    p.set_defaults(func=cmd_export_api)

    p = sub.add_parser("mapinfo", help="print the terrain profile of a base .SC2Map")
    p.add_argument("map")
    p.add_argument("--grid-only", action="store_true")
    p.add_argument("-o", "--output", help="write the profile to a file")
    p.add_argument("--check", metavar="STRAT", help="also check every point_xy of this .strat against the map")
    p.set_defaults(func=cmd_mapinfo)

    p = sub.add_parser("generate", help="generate variants with an LLM and build them on a base map")
    p.add_argument("--seed", required=True, help="seed .strat (keeps its intent.pattern)")
    p.add_argument("--base-map", help="target .SC2Map: terrain goes into the prompt, points are checked, map is packed")
    p.add_argument("--theme", default="variant", help="short label; also part of the variant name")
    p.add_argument("--brief", default="", help="free-text design brief for the model")
    p.add_argument("--param", action="append", default=[], metavar="KEY=VALUE",
                   help="designer parameter, repeatable (e.g. ally_race=zerg)")
    p.add_argument("-n", type=int, default=1, help="number of variants")
    p.add_argument("--provider", help="anthropic | openai | deepseek | qwen | ollama | <any OpenAI-compatible>")
    p.add_argument("--model")
    p.add_argument("--api-key")
    p.add_argument("--base-url", help="OpenAI-compatible endpoint")
    p.add_argument("--config", help="JSON provider config (default ~/.stratagemdsl/llm.json)")
    p.add_argument("--replay", action="append", metavar="FILE",
                   help="offline: use these .strat/.json files as the model's answers, in order")
    p.add_argument("--max-repairs", type=int, default=3)
    p.add_argument("--temperature", type=float, default=1.0)
    p.add_argument("--extra-body", default="", metavar="JSON",
                   help='extra request fields for OpenAI-compatible APIs, e.g. \'{"thinking": {"type": "disabled"}}\'')
    p.add_argument("--no-thinking", action="store_true",
                   help="turn the model's reasoning off (deepseek, qwen, zhipu; openai: low effort)")
    p.add_argument("--max-tokens", type=int, default=None,
                   help="output budget per call (default: 32000 for anthropic, 8096 otherwise)")
    p.add_argument("--no-tool-calling", action="store_true", help="ask for plain JSON instead of a tool call")
    p.add_argument("--loose", action="store_true", help="skip strict SC2 executability rules")
    p.add_argument("--compiler-root")
    p.add_argument("-o", "--out-dir", help="default build/llm/<seed stem>")
    p.set_defaults(func=cmd_generate)
    return ap


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
