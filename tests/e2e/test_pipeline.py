"""The pipeline runs each layer in order and stops where asked."""
import json

from stratagemdsl import pipeline
from stratagemdsl.cli import main as strat
from stratagemdsl.paths import REPO_ROOT

SEED = REPO_ROOT / "tests/fixtures/corpus/gmzz_20_enemy_loss_signal.strat"
LESSON = REPO_ROOT / "examples/learning/01_event_redeploy.strat"


def test_run_stops_at_the_requested_layer(tmp_path):
    r = pipeline.run(SEED, until="lower", out_dir=tmp_path)
    assert r.ok and list(r.stages) == ["parse", "check", "lower"]
    assert r.galaxy and r.compiled is None
    assert (tmp_path / "gmzz_20_enemy_loss_signal.galaxy").exists() and not (tmp_path / "gmzz_20_enemy_loss_signal.Triggers.xml").exists()
    assert json.loads((tmp_path / "result.json").read_text(encoding="utf-8"))["ok"]


def test_failure_is_recorded_not_raised(tmp_path):
    bad = tmp_path / "bad.strat"
    bad.write_text("strategy Broken {", encoding="utf-8")
    r = pipeline.run(bad, until="compile")
    assert not r.ok and r.failed_stage == "parse" and r.stages == {"parse": "failed"}


def test_full_compile_and_pack(tmp_path):
    r = pipeline.run(LESSON, until="pack", out_dir=tmp_path)
    assert r.ok, r.error
    assert r.map_result["status"] == "passed"
    assert (tmp_path / "01_event_redeploy.SC2Map").exists()


def test_cli_subcommands(tmp_path, capsys):
    assert strat(["parse", str(LESSON)]) == 0
    assert "EventRedeploy" in capsys.readouterr().out
    assert strat(["check", str(LESSON)]) == 0
    assert strat(["lower", str(LESSON), "-o", str(tmp_path)]) == 0
    assert (tmp_path / "01_event_redeploy.galaxy").exists()
    assert strat(["graph", str(LESSON), "-o", str(tmp_path)]) == 0
    assert (tmp_path / "01_event_redeploy.PlanGraph.mmd").exists()
    assert strat(["export-api", str(tmp_path / "api")]) == 0
    assert (tmp_path / "api/STRATEGY_TOOL.json").exists()


PETRI = REPO_ROOT / "examples/petri/sdjx_feint_cycle.strat"


def test_petri_plan_goes_all_the_way_to_a_map(tmp_path):
    r = pipeline.run(PETRI, until="pack", out_dir=tmp_path,
                     base_map=REPO_ROOT / "assets/base_maps/sdjx_te.SC2Map")
    assert r.ok, r.error
    assert not r.diagnostics
    summary = r.summary()
    assert summary["net"]["complete"] and summary["net"]["dead_transitions"] == []
    assert summary["map"]["status"] == "passed"
    for suffix in (".pnml", ".PetriNet.dot", ".net.json", ".galaxy", ".SC2Map"):
        assert (tmp_path / f"sdjx_feint_cycle{suffix}").exists(), suffix


def test_cli_net_command(capsys):
    assert strat(["net", str(PETRI)]) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["complete"] and report["net"]["places"] == 12
