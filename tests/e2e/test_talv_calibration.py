"""The CLI writes the allied agent-intent sidecar next to the compiled XML."""


from stratagemdsl.paths import REPO_ROOT
from stratagemdsl.frontend.antlr_parser import parse_file
from stratagemdsl.backend.intents import export_agent_intents
from stratagemdsl.cli import main as strat_main


ROOT = REPO_ROOT

DEMO = ROOT / "tests/fixtures/demos/jctq_talv_queue_timeout.strat"


def test_agent_intents_are_structured_and_cli_writes_sidecar(tmp_path):
    s = parse_file(DEMO)
    manifest = export_agent_intents(s)
    assert manifest['format'] == 'stratagemdsl.agent-intents.v1'
    assert manifest['intent_success']['kind'] == 'binary'
    assert all(item['call']['kind'] == 'call' for p in manifest['phase_intents']
               for item in p['actions']['items'])
    assert all(item['actor'] == 'escape_force' for p in manifest['phase_intents']
               for item in p['actions']['items'])
    assert strat_main(['compile', str(DEMO), '--out-dir', str(tmp_path)]) == 0
    assert (tmp_path / f'{DEMO.stem}.agent_intents.json').exists()
    assert (tmp_path / f'{DEMO.stem}.Triggers.xml').exists()
