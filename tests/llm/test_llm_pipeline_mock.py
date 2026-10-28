"""
Tests for the real-LLM pipeline glue, using a hand-built mock response
instead of a live API call (no LLM provider is reachable from CI/sandbox
environments). This proves the schema, prompt builder, repair loop, and
full downstream pipeline (unparse -> ANTLR4 -> Validator -> backend.galaxy
-> smac-ast compile) all work correctly; only the network call itself is
mocked.
"""

import json
from unittest import mock
import pytest

from stratagemdsl.paths import REPO_ROOT, compiler_root
from stratagemdsl.llm import pipeline as llm_pipeline
from stratagemdsl.llm.client import ProviderConfig
from stratagemdsl.frontend.antlr_parser import parse_source
from stratagemdsl.registry.schema import strategy_to_schema_dict


COMPILER_ROOT = compiler_root()

# A deliberately BROKEN variant: references a force ("ghost_force") never
# declared in `world`, so Validator must reject it (S-series undeclared-name
# error) and the repair loop must fire.
_BROKEN_SDJX_JSON = None

_VALID_SDJX_DSL = """strategy sdjx_mock_valid {
  world {
    force feint_force { side = ally; role = feint; }
    force main_force { side = ally; role = main; }
    force enemy_defenders { side = enemy; role = defense; }
    asset feint_nexus { side = ally; role = decoy_target; }
    asset main_nexus { side = ally; role = protected; }
    region main_threat_zone { role = feint_trigger; }
  }
  initial { alive(feint_force); alive(main_force); alive(enemy_defenders); alive(main_nexus); }
  intent {
    pattern TreeBlossom;
    primary alive(main_nexus);
    secondary alive(feint_force);
    success alive(main_nexus) and defeated(enemy_defenders);
    failure destroyed(main_nexus);
  }
  plan {
    start [watch];
    phase watch {
      purpose "Defenders watch the main approach.";
      actors [enemy_defenders]; focus [main_nexus];
    }
    phase feint_enters {
      purpose "A visible feint force moves toward the defended zone.";
      actors [feint_force]; focus [main_threat_zone]; do { move(feint_force, main_threat_zone); }
    }
    phase exploit {
      purpose "Main force attacks while defenders are distracted.";
      actors [main_force]; focus [enemy_defenders]; do { attack(main_force, enemy_defenders); } terminal success;
    }
    transition feint_seen: watch -> feint_enters { when true; priority 10; }
    transition defenders_distracted: feint_enters -> exploit {
      on enter(feint_force, main_threat_zone); when alive(feint_force); priority 10;
    }
  }
  binding sc2 {
    feint_force = unit_group(owner=1, unit_type="Medivac", count=2, spawn=point_id(1000000001));
    main_force = unit_group(owner=1, unit_type="Marine", count=10, spawn=point_id(1000000002));
    enemy_defenders = unit_group(owner=2, unit_type="Zealot", count=6, spawn=point_id(1000000003));
    feint_nexus = unit(owner=1, unit_type="Nexus", at=point_id(1000000004));
    main_nexus = unit(owner=1, unit_type="Nexus", at=point_id(1000000005));
    main_threat_zone = circle(center=point_id(1000000005), radius=8);
  }
}"""


def _broken_json():
    valid = parse_source(_VALID_SDJX_DSL)
    d = strategy_to_schema_dict(valid)
    # sabotage: reference an undeclared force in `intent.success`
    d["intent"]["success"] = {
        "kind": "call", "name": "alive", "args": [{"kind": "name", "name": "ghost_force"}]
    }
    return d


def _valid_json():
    valid = parse_source(_VALID_SDJX_DSL)
    return strategy_to_schema_dict(valid)


@pytest.mark.skipif(not COMPILER_ROOT.exists(), reason="galaxy compiler not available")
def test_repair_loop_recovers_from_invalid_first_attempt(tmp_path):
    calls = {"n": 0}

    def fake_call_llm_for_strategy(provider, prompt, temperature, max_tokens, use_tool_calling=True):
        calls["n"] += 1
        if calls["n"] == 1:
            raw = _broken_json()
            from stratagemdsl.registry.schema import StrategyS
            strategy = StrategyS.model_validate(raw).to_model()  # schema-valid, but semantically broken
            return strategy, raw, None
        else:
            raw = _valid_json()
            from stratagemdsl.registry.schema import StrategyS
            strategy = StrategyS.model_validate(raw).to_model()
            return strategy, raw, None

    with mock.patch.object(llm_pipeline, "call_llm_for_strategy", side_effect=fake_call_llm_for_strategy):
        provider = ProviderConfig(key="mock", api_key="x", model="mock-model")
        seed_path = REPO_ROOT / "tests/fixtures/seeds/sdjx.strat"
        record = llm_pipeline.run_llm_variant(
            provider=provider,
            seed_path=seed_path,
            theme="mock_test",
            compiler_root=str(COMPILER_ROOT),
            out_dir=tmp_path,
            max_repairs=2,
        )

    assert calls["n"] == 2, "expected exactly one repair round-trip"
    assert record["ok"] is True, record
    assert record["attempt_used"] == 1
    assert (tmp_path / "sdjx_mock_valid" / "sdjx_mock_valid.Triggers.xml").exists()


@pytest.mark.skipif(not COMPILER_ROOT.exists(), reason="galaxy compiler not available")
def test_exhausted_repairs_reports_failure_gracefully(tmp_path):
    def always_broken(provider, prompt, temperature, max_tokens, use_tool_calling=True):
        raw = _broken_json()
        from stratagemdsl.registry.schema import StrategyS
        strategy = StrategyS.model_validate(raw).to_model()
        return strategy, raw, None

    with mock.patch.object(llm_pipeline, "call_llm_for_strategy", side_effect=always_broken):
        provider = ProviderConfig(key="mock", api_key="x", model="mock-model")
        seed_path = REPO_ROOT / "tests/fixtures/seeds/sdjx.strat"
        record = llm_pipeline.run_llm_variant(
            provider=provider,
            seed_path=seed_path,
            theme="mock_test_fail",
            compiler_root=str(COMPILER_ROOT),
            out_dir=tmp_path,
            max_repairs=1,
        )

    assert record["ok"] is False
    assert record["stage"] == "exhausted_repairs"
    assert "ghost_force" in record["error"] or "S0" in record["error"]


def test_anthropic_call_retries_without_temperature_if_sdk_rejects_it():
    """Regression test: some anthropic SDK versions/model families don't
    accept `temperature` on messages.stream() at all (TypeError, not an API
    error). We must retry without it instead of hard-failing."""
    from stratagemdsl.llm import client as lvc

    calls = []

    class FakeContentBlock:
        type = "tool_use"
        input = {"ok": True}

    class FakeResponse:
        content = [FakeContentBlock()]

    class FakeStreamManager:
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def __iter__(self):
            return iter([])

        def get_final_message(self):
            return FakeResponse()

    class FakeMessages:
        def stream(self, **kwargs):
            calls.append(kwargs)
            if "temperature" in kwargs:
                raise TypeError("Messages.stream() got an unexpected keyword argument 'temperature'")
            return FakeStreamManager()

    class FakeClient:
        def __init__(self, api_key):
            self.messages = FakeMessages()

    import sys
    import types
    fake_anthropic_module = types.SimpleNamespace(Anthropic=FakeClient)
    with mock.patch.dict(sys.modules, {"anthropic": fake_anthropic_module}):
        provider = lvc.ProviderConfig(key="anthropic", api_key="x", model="claude-x")
        raw = lvc._anthropic_tool_call(provider, "prompt", temperature=0.7, max_tokens=100)

    assert raw == {"ok": True}
    assert len(calls) == 2, "expected one failed attempt with temperature, one retry without"
    assert "temperature" in calls[0]
    assert "temperature" not in calls[1]


def test_anthropic_call_uses_streaming_not_blocking_create():
    """Regression test: Anthropic requires `messages.stream(...)`, not the
    blocking `messages.create(...)`, once a request might run past 10
    minutes (real error message: "Streaming is required for operations
    that may take longer than 10 minutes"). Assert the client's `.stream`
    is actually what gets called, and that `.create` is never touched."""
    from stratagemdsl.llm import client as lvc

    class FakeContentBlock:
        type = "tool_use"
        input = {"ok": True, "via": "stream"}

    class FakeResponse:
        content = [FakeContentBlock()]

    class FakeStreamManager:
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def __iter__(self):
            return iter([])

        def get_final_message(self):
            return FakeResponse()

    class FakeMessages:
        def stream(self, **kwargs):
            return FakeStreamManager()

        def create(self, **kwargs):
            raise AssertionError("blocking messages.create() must not be used for the anthropic path")

    class FakeClient:
        def __init__(self, api_key):
            self.messages = FakeMessages()

    import sys
    import types
    fake_anthropic_module = types.SimpleNamespace(Anthropic=FakeClient)
    with mock.patch.dict(sys.modules, {"anthropic": fake_anthropic_module}):
        provider = lvc.ProviderConfig(key="anthropic", api_key="x", model="claude-x")
        raw = lvc._anthropic_tool_call(provider, "prompt", temperature=1.0, max_tokens=100)

    assert raw == {"ok": True, "via": "stream"}


def test_repair_prompt_carries_full_history_not_just_latest_error():
    """Regression test for the oscillation bug: attempt N+2's prompt must
    still mention an error from attempt N, even though attempt N+1 failed
    for a different reason -- otherwise the model can "forget" an earlier
    fix while addressing a new issue and flip-flop between two broken
    states forever."""
    history = [
        {"json": {"name": "v1"}, "error": "T060_ARITY: function 'strength' expects arity [1], got 2"},
        {"json": {"name": "v2"}, "error": "T010_EXPECT_BOOL: 'not' expects Bool, got Float"},
    ]
    prompt = llm_pipeline.build_repair_prompt("ORIGINAL PROMPT TEXT", history)
    assert "ORIGINAL PROMPT TEXT" in prompt
    assert "strength' expects arity" in prompt  # attempt #0's error still present
    assert "'not' expects Bool, got Float" in prompt  # attempt #1's error present
    assert "attempt #0" in prompt and "attempt #1" in prompt


def test_normalize_raw_response_fixes_envelope_wrap_and_stringified_fields():
    """Regression test for two real quirks seen from a live provider:
    (1) the whole payload wrapped in an extra {"input": {...}} envelope,
    (2) a nested list field ("bindings") emitted as a JSON-encoded string
    instead of real nested JSON. Both must be auto-fixed before Pydantic
    validation, individually and combined."""
    from stratagemdsl.frontend.antlr_parser import parse_file
    from stratagemdsl.registry.schema import strategy_to_schema_dict, StrategyS
    from stratagemdsl.llm.client import _normalize_raw_response

    seed = parse_file(str(REPO_ROOT / "tests/fixtures/seeds/wwjz.strat"))
    good = strategy_to_schema_dict(seed)

    wrapped = {"input": good}
    assert StrategyS.model_validate(_normalize_raw_response(wrapped)).name == "wwjz"

    corrupted = dict(good)
    corrupted["bindings"] = json.dumps(good["bindings"])
    fixed = StrategyS.model_validate(_normalize_raw_response(corrupted))
    assert len(fixed.bindings) == len(good["bindings"])

    both = {"input": corrupted}
    assert StrategyS.model_validate(_normalize_raw_response(both)).name == "wwjz"


def test_normalize_raw_response_does_not_corrupt_legitimate_json_looking_strings():
    """Regression test for F07 (external audit): a legitimate free-text
    field (e.g. Phase.purpose) that happens to start with '[' or '{' must
    NEVER be auto-decoded as JSON -- only whitelisted structural fields
    (bindings, world, args, ...) get that treatment. Before this fix,
    purpose = "[1, 2]" was silently turned into the list [1, 2], which then
    failed schema validation for a field that must be a string."""
    from stratagemdsl.frontend.antlr_parser import parse_file
    from stratagemdsl.registry.schema import strategy_to_schema_dict, StrategyS
    from stratagemdsl.llm.client import _normalize_raw_response

    seed = parse_file(str(REPO_ROOT / "tests/fixtures/seeds/wwjz.strat"))
    good = strategy_to_schema_dict(seed)
    good["plan"]["nodes"][0]["purpose"] = "[1, 2]"

    fixed = _normalize_raw_response(good)
    validated = StrategyS.model_validate(fixed)
    assert validated.plan.nodes[0].purpose == "[1, 2]"
