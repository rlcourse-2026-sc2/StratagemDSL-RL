"""`strat generate` end to end without a network: the replay provider answers."""
import json
import platform

import pytest

from stratagemdsl.cli import main as strat
from stratagemdsl.llm.config import resolve_provider
from stratagemdsl.paths import REPO_ROOT, base_maps_dir

SEED = REPO_ROOT / "examples/stratagems/dhls_18_enter_signal.strat"
GOOD = REPO_ROOT / "examples/demos/cerulean_lure_zerg_vs_protoss.strat"


@pytest.mark.skipif(platform.system() != "Linux", reason="packs a map with the bundled Linux StormLib")
def test_terrain_rejection_is_repaired_then_packed(tmp_path):
    # Answer 1 keeps the seed's point_id anchors (wrong map) -> terrain error fed back;
    # answer 2 uses point_xy on Cerulean Fall -> passes every layer and is packed.
    code = strat(["generate", "--seed", str(SEED), "--base-map", str(base_maps_dir() / "cerulean_fall_le.SC2Map"),
                  "--theme", "zvp", "--param", "ally_race=zerg", "--param", "enemy_race=protoss",
                  "--replay", str(SEED), "--replay", str(GOOD), "-o", str(tmp_path)])
    assert code == 0
    record = json.loads((tmp_path / "generation_records.json").read_text(encoding="utf-8"))[0]
    assert record["ok"] and record["attempt_used"] == 1
    assert [a["stage"] for a in record["attempts"]] == ["terrain"]
    assert "point_id is not portable" in record["failed_attempts"][0]["error"]
    assert record["map"]["status"] == "passed"
    prompt = (tmp_path / "prompt_zvp.txt").read_text(encoding="utf-8")
    assert "[TARGET MAP TERRAIN" in prompt and "ally_race: zerg" in prompt and "R4: center" in prompt
    out = tmp_path / record["name"]
    assert (out / f"{record['name']}.SC2Map").exists() and (out / f"{record['name']}.strat").exists()


def test_exhausted_repairs_report_the_last_error(tmp_path):
    code = strat(["generate", "--seed", str(SEED), "--base-map", str(base_maps_dir() / "cerulean_fall_le.SC2Map"),
                  "--replay", str(SEED), "--max-repairs", "1", "-o", str(tmp_path)])
    record = json.loads((tmp_path / "generation_records.json").read_text(encoding="utf-8"))[0]
    assert code == 1 and record["stage"] == "exhausted_repairs" and len(record["failed_attempts"]) == 2


def test_provider_resolution_precedence(tmp_path, monkeypatch):
    for var in ("STRAT_LLM_PROVIDER", "STRAT_LLM_MODEL", "STRAT_LLM_API_KEY", "STRAT_LLM_BASE_URL", "DEEPSEEK_API_KEY"):
        monkeypatch.delenv(var, raising=False)
    cfg = tmp_path / "llm.json"
    cfg.write_text(json.dumps({"default_provider": "deepseek",
                               "providers": {"deepseek": {"apikey": "file-key", "model": "file-model"}}}))
    p = resolve_provider(config=cfg)
    assert (p.key, p.api_key, p.model, p.base_url) == ("deepseek", "file-key", "file-model", "https://api.deepseek.com")
    monkeypatch.setenv("DEEPSEEK_API_KEY", "env-key")
    monkeypatch.setenv("STRAT_LLM_MODEL", "env-model")
    p = resolve_provider(config=cfg)
    assert (p.api_key, p.model) == ("env-key", "env-model")
    p = resolve_provider(model="flag-model", api_key="flag-key", config=cfg)
    assert (p.api_key, p.model) == ("flag-key", "flag-model")
    monkeypatch.delenv("STRAT_LLM_MODEL")
    with pytest.raises(ValueError, match="no model"):
        resolve_provider(provider="anthropic", api_key="k", config=tmp_path / "missing.json")
