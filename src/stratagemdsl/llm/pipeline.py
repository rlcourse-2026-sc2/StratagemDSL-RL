"""
Prompt construction + repair-loop pipeline for real-LLM StratagemDSL variant
generation.

Pipeline (same downstream steps as the simulated generator in
`tools/generators/generate_variants.py`, only the "propose a mutated Strategy" step
is swapped for a real model call):

    seed .strat
      -> ANTLR4 frontend (parse)
      -> build_prompt() [grammar cheat-sheet + one few-shot example
         (wwjz) + seed-as-JSON + creative brief]
      -> llm.client.call_llm_for_strategy()
      -> unparse -> ANTLR4 re-parse -> semantic checks (strict SC2 when asked)
         -> terrain check of every point_xy against the base map (when given)
         -> backend.galaxy.lower_to_galaxy -> compiler.compile_galaxy_source
      -> on any failure: build_repair_prompt() with the concrete error and
         the model's own previous JSON, call again (bounded retries)
      -> finally, with a base map: pack the .SC2Map and read it back
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from stratagemdsl.frontend.antlr_parser import parse_file as antlr_parse_file, parse_source as antlr_parse_source
from stratagemdsl.registry.builtins import ACTIONS, EVENTS, FUNCTIONS
from stratagemdsl.registry.contracts import contracts
from stratagemdsl.frontend.unparse import unparse
from stratagemdsl.semantics.validator import Validator
from stratagemdsl import pipeline as compile_pipeline
from stratagemdsl.backend.galaxy import lower_to_galaxy, LoweringError
from stratagemdsl.compiler.galaxycc_adapter import compile_galaxy_source
from stratagemdsl.registry.schema import strategy_to_schema_dict
from stratagemdsl.llm.client import ProviderConfig, call_llm_for_strategy
from stratagemdsl.core.model import Strategy

_FEWSHOT_STRAT_SOURCE = """strategy wwjz {
  world {
    force relief_force { side = ally; role = relief; }
    force enemy_siege_force { side = enemy; role = siege; }
    asset besieged_base { side = ally; role = protected; }
    asset enemy_home { side = enemy; role = critical; }
    region enemy_home_zone { role = threat_trigger; }
    region interception_zone { role = exploit; }
  }
  initial {
    alive(relief_force); alive(enemy_siege_force); alive(besieged_base); alive(enemy_home);
    targeting(enemy_siege_force, besieged_base);
  }
  intent {
    pattern IndirectRelief;
    primary base_relieved;
    secondary alive(besieged_base);
    success base_relieved and alive(besieged_base) and (destroyed(enemy_home) or defeated(enemy_siege_force));
    failure destroyed(besieged_base);
  }
  semantics {
    derive rear_threat_active = in_region(relief_force, enemy_home_zone);
    derive base_relieved = not targeting(enemy_siege_force, besieged_base);
  }
  plan {
    start [siege];
    phase siege {
      purpose "Enemy force is besieging our Nexus; direct relief is too slow.";
      actors [enemy_siege_force]; focus [besieged_base]; do { attack(enemy_siege_force, besieged_base); }
    }
    phase threaten_home {
      purpose "Threaten the enemy rear instead of returning directly.";
      actors [relief_force]; focus [enemy_home]; do { move(relief_force, enemy_home_zone); }
    }
    phase force_redeploy {
      purpose "Force the siege force to abandon the Nexus and retarget.";
      actors [enemy_siege_force]; focus [enemy_home, relief_force];
    }
    phase intercept {
      purpose "Exploit enemy redeployment and attack the returning force.";
      actors [relief_force]; focus [enemy_siege_force]; do { attack(relief_force, enemy_siege_force); } terminal success;
    }
    transition choose_indirect_relief: siege -> threaten_home { when true; priority 10; }
    transition rear_threat_causes_retarget: threaten_home -> force_redeploy {
      on enter(relief_force, enemy_home_zone); when alive(besieged_base);
      do { retarget(enemy_siege_force, relief_force); } priority 10;
    }
    transition redeployment_opens_window: force_redeploy -> intercept {
      when base_relieved and retargeted(enemy_siege_force, relief_force); priority 10;
    }
  }
  binding sc2 {
    relief_force = unit_group(owner=1, unit_type="Zealot", count=7, spawn=point_xy(53.4807, 49.561));
    enemy_siege_force = unit_group(owner=2, composition=[unit(unit_type="Hellion", count=8), unit(unit_type="Marine", count=6)], spawn=point_xy(34.9594, 41.8471));
    besieged_base = unit(owner=1, unit_type="Nexus", at=point_xy(24.0915, 55.7783));
    enemy_home = unit(owner=2, unit_type="CommandCenter", at=point_xy(69.2932, 19.5087));
    enemy_home_zone = circle(center=point_xy(69.2932, 19.5087), radius=5);
    interception_zone = circle(center=point_xy(69.2932, 19.5087), radius=7);
  }
}"""
_FEWSHOT_GLOSS = (
    "wwjz (\u56f4\u9b4f\u6551\u8d75 / Besiege Wei to Rescue Zhao): an enemy siege force pins "
    "our Nexus; instead of returning directly, a relief force threatens the enemy's own home "
    "base so the siege force is forced to abandon the siege and redeploy, at which point the "
    "relief force intercepts it."
)


def _fewshot_schema_json() -> str:
    from stratagemdsl.frontend.antlr_parser import parse_source
    example = parse_source(_FEWSHOT_STRAT_SOURCE)
    return json.dumps(strategy_to_schema_dict(example), indent=2)


def _render_signatures(table: dict) -> list[str]:
    """Render each predicate/event/action with EXACT per-position argument
    types (merging same-arity overloads into a `TypeA|TypeB` union at each
    position) instead of a bare name list. The model kept guessing wrong
    arities (e.g. calling `strength(a, b)` when `strength` only takes one
    Force, or `hold(force, region)` when `hold` only takes one Force) when
    only given names -- exact signatures directly target that failure mode.
    """
    lines = []
    for name, sigs in sorted(table.items()):
        by_arity: dict[int, list[tuple]] = {}
        ret_types: set = set()
        for sig in sigs:
            by_arity.setdefault(len(sig.args), []).append(sig.args)
            ret_types.add(sig.returns)
        variants = []
        for arity, arglists in sorted(by_arity.items()):
            merged = []
            for i in range(arity):
                types_at_i = sorted({al[i] for al in arglists})
                merged.append("|".join(types_at_i))
            variants.append(f"{name}({', '.join(merged)})")
        ret = "|".join(sorted(ret_types))
        lines.append(" OR ".join(variants) + f" -> {ret}")
    return lines


def _pattern_lines() -> str:
    """Role lists of the patterns with a causal definition, for the cheatsheet."""
    from stratagemdsl.semantics.patterns.library import PATTERNS
    rows = [f"{p.name}: " + ", ".join(f"{r.name} ({r.type_name})" for r in p.roles) for p in PATTERNS.values()]
    return ("For these patterns, `pattern_bindings` maps EVERY role to a world entity of that type "
            "(the checker proves the pattern's causal chain from them; keep the seed's bindings "
            "unless you rename the entities):\n    " + "\n    ".join(rows))


def _grammar_cheatsheet(map_context_available: bool = False) -> str:
    func_lines = "\n  ".join(_render_signatures(FUNCTIONS))
    event_lines = "\n  ".join(_render_signatures(EVENTS))
    action_lines = "\n  ".join(_render_signatures(ACTIONS))
    pattern_lines = _pattern_lines()
    scope_lines = "\n  ".join(
        f"{spec.namespace} {spec.name}: {spec.backend}; {spec.prerequisites}; "
        f"issued={spec.issue_evidence or 'n/a'}; effect={spec.effect_evidence or 'not established'}"
        for spec in contracts() if spec.alias_of or spec.backend != "lowered"
        or (spec.namespace == "action" and spec.name in {"move", "retreat", "retarget", "hold", "cast"})
    )
    if map_context_available:
        point_rule = """2. A [TARGET MAP TERRAIN] block appears below with real coordinate data for the specific map
   this variant will be packed into -- so use `point_xy(x, y)` for EVERY spawn=/at=/source=/center=
   location in this variant, with NO exceptions, INCLUDING entities you are otherwise keeping
   structurally unchanged from the seed. Do NOT copy forward any `point_id(N)` value from the seed's
   bindings, even for an entity whose role/composition you didn't change -- the seed's point_ids are
   anchors on a DIFFERENT, unrelated map and are not valid on this one; reusing one verbatim (or
   offsetting it) fails at RUNTIME in-game with "Could not get 'inPos' from parameter in
   'sUnitCreate'", not at compile time, so this mistake is invisible until someone actually loads the
   packed map. Every coordinate you pick must fall inside the "Playable region" bounds given below,
   on a walkable cell as defined by the grid legend in that block (never '#'; structures only on
   level-digit cells, clear of ramps '/' and doodads 'x')."""
    else:
        point_rule = """2. No target-map terrain data is available. For unchanged locations on the SAME map,
   preserve the seed's validated coordinates and prefer `point_xy(x, y)` when they are known.
   Preserve an existing `point_id(N)` only when it is confirmed in that map's Objects file; do NOT
   generate random IDs or numeric offsets from known IDs. For a DIFFERENT target map, a valid
   coordinate must come from its actual playable bounds and terrain; never guess a new coordinate
   merely to fill the schema. An unknown `point_id` can pass compilation and still fail at runtime."""
    return f"""StratagemDSL structure (as JSON matching the provided schema):
- world: force/asset/region/route entities, each with side (ally|enemy|neutral) and a free-text role.
- initial: boolean facts true at scenario start (usually alive(...) calls).
- intent: pattern name + primary/secondary/success/failure boolean expressions.
  {pattern_lines}
- derived: named Bool/Int/Float expressions computable from world state, expanded when referenced.
- plan: a reactive graph of `phase` and `join` nodes plus `transition` edges
  (source -> target, optional `on` event, optional `when` guard, optional `do` actions, `priority`).
- bindings: maps each world entity / plan concept to an sc2 backend construct:
  unit_group(owner, unit_type|composition=[unit(unit_type,count),...], count, spawn=point_xy(x,y)),
  unit(owner, unit_type, at=point_xy(x,y)), group_slice(owner, unit_type, role, source=point_xy(x,y)),
  circle(center=point_xy(x,y), radius=R), and optional setup(...) for map-level tweaks.

Legal boolean/numeric predicates -- EXACT arity and argument types, calling with the wrong number
or type of arguments is a hard validation error:
  {func_lines}

Legal transition events (used inside `on ...`) -- exact arity/types, same rule:
  {event_lines}

Legal plan actions (used inside `do {{...}}`) -- exact arity/types, same rule:
  {action_lines}

API execution scope from the same registry as the checker and tool schema:
  {scope_lines}
`path_passable` is a compatibility alias for `center_passable` and tests only the center.
`apparent_count` is a compatibility alias for `player_unit_count`, which counts
all live units matched by the default filter for the bound force's owner across
the map, not visibility to an observer.
`path_connected(region_a, region_b)` checks ground connectivity between centers;
neither this nor `center_passable` proves a particular unit can reach a point.
`mission_time()` returns absolute game mission seconds; `after(seconds)` compares the
same clock and is a predicate for `when`, not an `on` event. For a timeout,
keep a live phase with an outgoing `when after(600)` transition.
`unit_became_idle(force)` reports one member becoming idle, not whole-group
completion. `unit_attacked(victim, attacker)` and `unit_died(victim, killer)`
accept an optional Force in the second positional argument; named `by=` is not
part of the current event grammar.

Critical constraints:
1. Only reference world/plan-node names that you declare. Every force/asset/region referenced in
   intent, derived, plan, or bindings must be declared in `world`, and every phase/join id used in
   `plan.start` or a transition's source/target must exist in `plan.nodes`.
{point_rule}
3. Only reuse a unit type on an ability-specific action (cast/set_mode/ability_completed/ability_cast)
   if that pairing already exists in the seed or is a standard SC2 pairing (SiegeTank/SiegeTankSieged
   <-> "Unsiege"; a spellcaster like Sentry/HighTemplar <-> "Hallucination"/"ForceField"; a burrowing
   Zerg ground unit <-> "Burrow"; Infestor <-> "NeuralParasite"; SupplyDepot <-> "SupplyDepotRaise"/
   "SupplyDepotLower"). Never move such an action onto an unrelated unit type.
4. Allied (side=ally) forces' move/attack/etc. in `plan` express strategic INTENT for evaluation only
   -- they will not be issued as literal in-game orders to the player-controlled side. Enemy-side
   actions are what actually gets compiled into trigger logic. Write the allied intent anyway; it is
   part of the scenario's designed fiction and is exported in `agent_intents.json`.
   In an enemy-side `do sequence` block, orders to the same actor use Replace for the
   first order and AddToEnd for later orders; `do parallel` uses Replace for each.
   Queued orders still need independent observations to establish arrival or effect.
5. `not X` requires X to be a Bool-typed expression -- a predicate that returns Bool (alive, destroyed,
   defeated, in_region, targeting, ...), never one that returns Int/Float/Any (count, distance,
   strength, killed_in, ...). To negate a numeric comparison, write `not (count(F) >= 3)` or
   `count(F) < 3`, never `not count(F)`.
6. Every transition's `priority` must be unique among transitions sharing the same `source` phase/join
   (two transitions leaving the same node cannot both have priority 10, for example).
7. Multiple transitions leaving the SAME source (whether eventless, or sharing the exact same `on`
   event) are MUTUALLY EXCLUSIVE at runtime -- only the lowest-`priority`-number one whose guard holds
   ever actually fires, the others never do. Never feed an `all` (or `atleast(k)` with k>1) join with
   inputs that only become reachable through DIFFERENT branches of one such exclusive fork -- since only
   one branch can ever run, the join can never collect enough distinct arrivals and the plan permanently
   deadlocks there. If two lines of action are meant to genuinely run in parallel (e.g. a vanguard
   force and a reserve force each doing their own thing before reuniting at a join), give them
   independent starting points instead -- list BOTH phases in `plan.start` -- rather than branching to
   both from one shared source.
8. Every non-terminal phase (one without `terminal: success|failure`) must have at least one outgoing
   transition, or the plan graph can get permanently stuck there.
9. `targeting`, `retargeted`, `relieved`, and `strength` are valid for `initial`/`intent`/`derive`
   (they describe the scenario for evaluation), but CANNOT be lowered into a real Galaxy trigger guard
   yet -- a transition whose `when` guard uses them (directly or via a `derive`) will hard-fail to
   compile. If a transition needs to react to "X got retargeted" or "Y's targeting changed", express it
   the same way the seed corpus does: attach the state-change to a real `on` event instead (e.g. do the
   `retarget(...)` action on the transition triggered `on enter(force, region)`, and have the NEXT
   transition react to reaching that phase or to a genuinely observable event like `unit_died`, rather
   than re-checking `targeting`/`retargeted` in a bare `when`).
10. A `when`-only transition with NO `on` event is checked on a 1-second game-time poll when its
   guard depends on live state or time, including `after`/`mission_time`. Unconditional forward
   transitions may be folded into activation. An `on` event is more direct for a specific
   occurrence, but an event that happens before the source phase activates is not replayed.
11. Keep the JSON strictly within the given schema: no extra fields, no missing required fields.
12. (v0.6, optional) The plan is a Petri net. A transition may list several arcs in `inputs` /
   `outputs` (each {{place, weight, kind}}): several outputs fork into parallel branches, several
   inputs synchronise them without a join node, kind "read" requires tokens without taking them,
   kind "inhibit" requires the place to be empty. `place` nodes ({{node_type: "place", tokens,
   capacity}}) hold budgets and counters; a `repeatable` phase may be re-entered (needed for loops).
   Every loop must spend a bounded token place, and every place must stay bounded. Leave `inputs` /
   `outputs` empty for the classic single source -> target form.
"""


def _note_attempt(record: dict, item: dict) -> None:
    """Record a rejected attempt and report it right away (not only at the end)."""
    from stratagemdsl.llm import client
    record.setdefault("attempts", []).append(item)
    lines = (item.get("error") or "").splitlines()
    verb = "note" if str(item.get("error", "")).startswith("non-fatal") else "rejected"
    client.progress(f"  attempt {item['attempt']}: {verb} at {item['stage']}: {' | '.join(lines[:3])[:240]}")


def build_prompt(seed: Strategy, theme: str, brief: str = "", map_context: str = "") -> str:
    cheatsheet = _grammar_cheatsheet(map_context_available=bool(map_context))
    seed_json = json.dumps(strategy_to_schema_dict(seed), indent=2)
    brief_line = f"\nAdditional creative brief from the designer: {brief}\n" if brief else ""

    if seed.name == "wwjz":
        fewshot_block = ""  # the seed itself already demonstrates the exact shape
    else:
        fewshot_block = f"""
Worked example of the schema shape ({_FEWSHOT_GLOSS}):
{_fewshot_schema_json()}
"""

    if map_context:
        map_context_block = f"""
[TARGET MAP TERRAIN -- real data extracted from the actual .SC2Map this variant will be packed
into. Use this to place EVERY point_xy(x, y) you write: pick coordinates inside the "Playable
region" bounds below, landing on a walkable cell as defined by the grid legend (never '#';
structures only on level-digit cells). This is not guesswork -- a point_xy that lands off the walkable terrain will spawn
nothing there and can break the scenario at runtime, exactly like an invalid point_id does. Prefer
point_xy(x, y) over point_id(N) for every location in this variant, since point_id only works if
that exact id happens to already be placed on this specific map, which the seed's ids generally
are not.]
{map_context}
"""
    else:
        map_context_block = ""

    return f"""You are designing a new StarCraft II multi-agent benchmark scenario variant in
StratagemDSL, a structured strategy DSL (world + initial state + intent + reactive plan graph +
sc2 binding). You will emit your answer by calling the `{{tool_name}}` tool with a JSON object
matching the provided schema exactly.

{cheatsheet}
{fewshot_block}
Here is the seed scenario "{seed.name}" you are producing a variant of, as schema JSON:
{seed_json}
{map_context_block}
Your task: design a genuinely different tactical variant of this stratagem -- theme: "{theme}".
Keep the same core stratagem pattern (the `intent.pattern`) but change the plan graph, force
composition, and/or thresholds meaningfully; do not just copy the seed unchanged. Give the new
strategy a distinct `name` (e.g. "{seed.name}_{theme}").
{brief_line}
Call the tool now with your complete variant.
"""


def build_repair_prompt(original_prompt: str, history: list[dict]) -> str:
    """`history` is the full list of {"json": ..., "error": ...} pairs from
    every failed attempt so far (not just the most recent one) -- without
    this, a model that fixes issue A while re-introducing issue B on attempt
    N+1 has no memory of A by attempt N+2 and can oscillate indefinitely
    instead of converging."""
    attempts_block = "\n\n".join(
        f"--- Your attempt #{i} ---\n{json.dumps(h['json'], indent=2)}\n"
        f"FAILED with:\n{h['error']}"
        for i, h in enumerate(history)
    )
    return f"""{original_prompt}

You have already tried {len(history)} time(s) and every attempt failed. Here is the full history,
in order -- do not reintroduce a problem that was already flagged in an earlier attempt even if
you're currently fixing a different one:

{attempts_block}

Fix ALL of the problems above and call the tool again with a complete, corrected JSON object
(not a diff, not a partial patch -- the full strategy).
"""


def run_llm_variant(
    provider: ProviderConfig,
    seed_path: str | Path,
    theme: str,
    compiler_root: str | Path,
    out_dir: str | Path,
    brief: str = "",
    temperature: float = 1.0,
    max_tokens: Optional[int] = None,
    max_repairs: int = 2,
    use_tool_calling: bool = True,
    map_context: str = "",
    base_map: str | Path | None = None,
    strict: bool = False,
    stormlib: str | Path | None = None,
) -> dict:
    """Generate one variant. With ``base_map`` the prompt receives that map's
    terrain profile, every point_xy is checked against it inside the repair
    loop, and the result is packed into a copy of the map. ``strict`` applies
    the strict SC2 executability rules (recommended for anything you pack)."""
    seed_path = Path(seed_path)
    out_dir = Path(out_dir)
    record: dict = {"seed": seed_path.name, "theme": theme, "provider": provider.key, "model": provider.model,
                    "base_map": str(base_map) if base_map else None, "strict": strict}
    profile = None
    if base_map is not None:
        from stratagemdsl.packaging.terrain import load_profile
        try:
            profile = load_profile(base_map, stormlib=Path(stormlib) if stormlib else None)
        except Exception as e:
            record.update(stage="read_base_map", ok=False, error=f"{type(e).__name__}: {e}")
            return record
        map_context = map_context or profile.render_context()

    try:
        seed_strategy = antlr_parse_file(seed_path)
    except Exception as e:
        record.update(stage="parse_seed", ok=False, error=str(e))
        return record

    prompt = build_prompt(seed_strategy, theme, brief, map_context).replace("{tool_name}", "emit_stratagem_variant")
    record["prompt_chars"] = len(prompt)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / f"prompt_{theme}.txt").write_text(prompt, encoding="utf-8")
    history: list[dict] = []  # [{"json": ..., "error": ...}, ...] across ALL failed attempts so far

    for attempt in range(max_repairs + 1):
        call_prompt = prompt if attempt == 0 else build_repair_prompt(prompt, history)
        strategy, raw_json, err = call_llm_for_strategy(
            provider, call_prompt, temperature=temperature, max_tokens=max_tokens,
            use_tool_calling=use_tool_calling,
        )
        if err is not None:
            history.append({"json": raw_json, "error": err})
            _note_attempt(record, {"attempt": attempt, "stage": "llm_call_or_schema", "error": err})
            continue

        variant_dir = out_dir / strategy.name
        try:
            text = unparse(strategy)
        except Exception as e:
            error = f"unparse failed: {e}"
            history.append({"json": raw_json, "error": error})
            _note_attempt(record, {"attempt": attempt, "stage": "unparse", "error": error})
            continue

        try:
            reparsed = antlr_parse_source(text)
        except SyntaxError as e:
            error = f"ANTLR4 re-parse failed (the emitted JSON did not round-trip to valid DSL text): {e}"
            history.append({"json": raw_json, "error": error})
            _note_attempt(record, {"attempt": attempt, "stage": "antlr_reparse", "error": error})
            continue

        bag = compile_pipeline.validate(reparsed, strict=True).diagnostics if strict else Validator(reparsed).validate()
        if bag.has_errors:
            error = "StratagemDSL semantic validation failed:\n" + "\n".join(str(d) for d in bag.items)
            history.append({"json": raw_json, "error": error})
            _note_attempt(record, {"attempt": attempt, "stage": "validate", "error": error})
            continue

        if profile is not None:
            from stratagemdsl.packaging.terrain import check_bindings
            problems = check_bindings(reparsed, profile)
            if problems:
                error = (f"Coordinates do not fit the base map {profile.path.name}:\n" + "\n".join(problems)
                         + "\nMove each listed point to the nearest valid spot given for it (or to another open point "
                         "from the [TARGET MAP TERRAIN] block). Keep every coordinate that is not listed unchanged, "
                         "and keep regions and spawns consistent with the moved structures.")
                history.append({"json": raw_json, "error": error})
                _note_attempt(record, {"attempt": attempt, "stage": "terrain", "error": error})
                continue

        try:
            galaxy_src, notes = lower_to_galaxy(reparsed)
        except LoweringError as e:
            error = f"Galaxy lowering failed: {e}"
            history.append({"json": raw_json, "error": error})
            _note_attempt(record, {"attempt": attempt, "stage": "lower_to_galaxy", "error": error})
            continue

        variant_dir.mkdir(parents=True, exist_ok=True)
        (variant_dir / f"{strategy.name}.strat").write_text(text, encoding="utf-8")
        galaxy_path = variant_dir / f"{strategy.name}.galaxy"
        try:
            result = compile_galaxy_source(galaxy_src, compiler_root=compiler_root, source_path=galaxy_path)
        except Exception as e:
            error = f"smac-ast compile crashed: {type(e).__name__}: {e}"
            history.append({"json": raw_json, "error": error})
            _note_attempt(record, {"attempt": attempt, "stage": "smac_ast_compile", "error": error})
            continue

        if not result.judge_ok:
            error = f"smac-ast semantic judge failed: {result.judge_result}"
            history.append({"json": raw_json, "error": error})
            _note_attempt(record, {"attempt": attempt, "stage": "smac_ast_judge", "error": error})
            continue

        (variant_dir / f"{strategy.name}.Triggers.xml").write_text(result.trigger_xml or "", encoding="utf-8")
        (variant_dir / f"{strategy.name}.PlacedObjects.xml").write_text(result.placed_objects_xml or "", encoding="utf-8")
        (variant_dir / f"{strategy.name}.TriggerText.txt").write_text(result.trigger_text or "", encoding="utf-8")
        from stratagemdsl.backend.intents import agent_intents_json
        (variant_dir / f"{strategy.name}.agent_intents.json").write_text(agent_intents_json(reparsed), encoding="utf-8")

        # Plan graph: written to disk unconditionally (works even if the
        # browser-side mermaid.js CDN import glitches -- see views/plangraph.py).
        try:
            from stratagemdsl.views.plangraph import build_graph_model, to_dot, to_mermaid
            graph_model = build_graph_model(reparsed)
            (variant_dir / f"{strategy.name}.dot").write_text(to_dot(graph_model), encoding="utf-8")
            (variant_dir / f"{strategy.name}.mmd").write_text(to_mermaid(graph_model), encoding="utf-8")
        except Exception as e:
            _note_attempt(record, 
                {"attempt": attempt, "stage": "plangraph_export", "error": f"non-fatal: {e}"}
            )

        # AST views: own try/except, independent of the plan graph one above
        # -- a bug in one must never silently take the other down too (this
        # is exactly the failure mode that bit the web app's plangraph/AST
        # panels earlier when they shared a single try/except).
        try:
            import json as _json
            from stratagemdsl.frontend.pretty import pretty as ast_pretty_print
            from stratagemdsl.registry.schema import strategy_to_schema_dict
            (variant_dir / f"{strategy.name}.ast.txt").write_text(ast_pretty_print(reparsed), encoding="utf-8")
            (variant_dir / f"{strategy.name}.ast.json").write_text(
                _json.dumps(strategy_to_schema_dict(reparsed), indent=2, ensure_ascii=False), encoding="utf-8"
            )
        except Exception as e:
            _note_attempt(record, 
                {"attempt": attempt, "stage": "ast_export", "error": f"non-fatal: {e}"}
            )

        if base_map is not None:
            try:
                record["map"] = compile_pipeline.pack(galaxy_src, result, variant_dir / f"{strategy.name}.SC2Map",
                                                      base_map=Path(base_map),
                                                      stormlib=Path(stormlib) if stormlib else None)
            except Exception as e:
                record["failed_attempts"] = history  # every rejected JSON with the error fed back
                record.update(stage="pack", ok=False, name=strategy.name, out_dir=str(variant_dir),
                              error=f"map packing failed: {type(e).__name__}: {e}")
                return record

        record["failed_attempts"] = history  # every rejected JSON with the error fed back
        record.update(stage="done", ok=True, name=strategy.name, attempt_used=attempt,
                       notes=sorted(set(notes)), out_dir=str(variant_dir))
        return record

    record["failed_attempts"] = history  # every rejected JSON with the error fed back
    record.update(stage="exhausted_repairs", ok=False, error=history[-1]["error"] if history else "unknown error")
    return record
