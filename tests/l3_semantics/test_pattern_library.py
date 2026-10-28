"""Pattern library consistency and the report status (PASS / FAIL / NOT CHECKED)."""
from stratagemdsl.frontend.lark_parser import parse_file, parse_source
from stratagemdsl.paths import REPO_ROOT
from stratagemdsl.semantics.patterns.facts import ACTION_FACT_KINDS, EVENT_FACT_KINDS
from stratagemdsl.semantics.patterns.library import PATTERNS, UNCHECKED_PATTERNS
from stratagemdsl.semantics.patterns.report import format_pattern_report
from stratagemdsl.semantics.validator import Validator

SEEDS = REPO_ROOT / "tests/fixtures/seeds"


def _check(text: str):
    v = Validator(parse_source(text))
    bag = v.validate()
    return v.pattern_report, {d.code for d in bag.items}, bag


def test_rules_and_obligations_only_use_declared_roles_and_reachable_fact_kinds():
    for p in PATTERNS.values():
        roles = {r.name for r in p.roles}
        derived = {d.fact.kind for r in p.interpretations for d in r.derive}
        for rule in p.interpretations:
            assert rule.scope in ("phase", "transition", "any"), p.name
            pats = [fp for _, fp in rule.match] + ([rule.event] if rule.event else []) + [d.fact for d in rule.derive]
            used = {a[1:] for fp in pats for a in fp.args if a.startswith("$")} | {x for pair in rule.distinct for x in pair}
            assert used <= roles, (p.name, used - roles)
            labels = {"new", "event"} | {label for label, _ in rule.match}
            for d in rule.derive:
                assert "_" not in d.fact.args, (p.name, d.fact)
                for link in d.links:
                    assert {link.source, link.target} <= labels, (p.name, link)
        for ob in p.obligations:
            for fp in (ob.source, ob.target):
                assert fp.kind in ACTION_FACT_KINDS | EVENT_FACT_KINDS | derived, (p.name, fp.kind)
                assert {a[1:] for a in fp.args if a.startswith("$")} <= roles, (p.name, fp)
    assert not set(PATTERNS) & UNCHECKED_PATTERNS


def test_checked_pattern_reports_pass_and_fail():
    text = (SEEDS / "sdjx.strat").read_text(encoding="utf-8")
    report, _, _ = _check(text)
    assert report.status == "PASS" and report.checked
    report, codes, _ = _check(text.replace("retarget(defenders, enemy_main);", "retarget(defenders, enemy_expansion);"))
    assert report.status == "FAIL" and "C101_FEINT_THREAT_TO_RELOCATION" in codes
    assert "Status : FAIL" in format_pattern_report(report)


def test_pattern_without_causal_definition_is_not_checked_and_not_flagged():
    report, codes, _ = _check((SEEDS / "jctq.strat").read_text(encoding="utf-8"))
    assert report.pattern == "EscapeConcealment"
    assert report.passed and not report.checked and report.status == "NOT CHECKED"
    assert not any(c.startswith("C09") for c in codes)
    assert "Status : NOT CHECKED" in format_pattern_report(report)


def test_unbound_pattern_is_not_checked():
    text = (SEEDS / "sdjx.strat").read_text(encoding="utf-8")
    start = text.index("pattern Feint {")
    text = text[:start] + "pattern Feint;" + text[text.index("}", start) + 1:]
    report, codes, _ = _check(text)
    assert "C090_PATTERN_UNBOUND" in codes
    assert report.status == "NOT CHECKED" and report.reason == "no role bindings"


def test_unknown_pattern_name_warns_and_suggests():
    text = (SEEDS / "sdjx.strat").read_text(encoding="utf-8").replace("pattern Feint", "pattern Fient")
    report, codes, bag = _check(text)
    assert "C096_PATTERN_UNKNOWN" in codes and not bag.has_errors
    assert "Did you mean 'Feint'?" in next(str(d) for d in bag.items if d.code == "C096_PATTERN_UNKNOWN")
    assert report.status == "NOT CHECKED"
    report, codes, _ = _check(text.replace("pattern Fient", "pattern feint"))
    assert "C096_PATTERN_UNKNOWN" in codes      # names are case-sensitive


def test_every_pattern_name_in_the_repository_is_known():
    import re
    names = set()
    for f in list(REPO_ROOT.glob("tests/fixtures/**/*.strat")) + list(REPO_ROOT.glob("examples/**/*.strat")):
        names |= set(re.findall(r"\bpattern\s+([A-Za-z_]\w*)", f.read_text(encoding="utf-8")))
    assert names <= set(PATTERNS) | UNCHECKED_PATTERNS, names - set(PATTERNS) - UNCHECKED_PATTERNS


# ---------------------------------------------------------------- Trap
import re

import pytest

TRAP_CODES = {"C141_TRAP_COMMIT_TO_CLOSURE", "C142_TRAP_CLOSURE_TO_EXPLOIT"}


@pytest.mark.parametrize("rel", [
    "tests/fixtures/seeds/gmzz.strat",                    # depot wall raised; losses observed
    "tests/fixtures/seeds/swct.strat",                    # ramp blocked; Hatchery attacked
    "examples/petri/swct_fork_trap.strat",          # commitment observed by an enter event
    "tests/fixtures/variants/gmzz_two_stage_gate.strat",
    "tests/fixtures/variants/swct_counted_return.strat",
])
def test_trap_examples_have_both_witnesses(rel):
    v = Validator(parse_file(REPO_ROOT / rel))
    v.validate()
    assert v.pattern_report.status == "PASS", [str(d) for d in v.pattern_report.diagnostics]
    assert {w.code for w in v.pattern_report.witnesses} == TRAP_CODES


@pytest.mark.parametrize("path", sorted((REPO_ROOT / "tests/fixtures/pattern_negative").glob("*.strat")), ids=lambda p: p.stem)
def test_pattern_negative_examples_fail_with_the_codes_in_their_header(path):
    text = path.read_text(encoding="utf-8")
    expected = set(re.findall(r"\b(C\d\d\d_[A-Z_]+)", text.split("strategy", 1)[0]))
    assert expected, "header names no expected code"
    report, codes, _ = _check(text)
    assert report.status == "FAIL"
    assert expected <= codes, sorted(codes)


def test_trap_closure_must_follow_the_commitment_in_a_sequence():
    text = (SEEDS / "swct.strat").read_text(encoding="utf-8")
    text = text.replace("do { block(control_force, ramp_block_zone); }", "")
    commit = "do { retarget(enemy_defenders, enemy_home); } priority 10;"   # transition proximity_commit
    assert text.count(commit) == 1
    first = text.index(commit)
    ordered = text[:first] + "do { retarget(enemy_defenders, enemy_home); block(control_force, ramp_block_zone); } priority 10;" + text[first + len(commit):]
    report, codes, _ = _check(ordered)
    assert "C141_TRAP_COMMIT_TO_CLOSURE" not in codes, report.diagnostics
    reversed_ = text[:first] + "do { block(control_force, ramp_block_zone); retarget(enemy_defenders, enemy_home); } priority 10;" + text[first + len(commit):]
    _, codes, _ = _check(reversed_)
    assert "C141_TRAP_COMMIT_TO_CLOSURE" in codes


def test_trap_way_out_binding_decides_what_counts_as_closure():
    text = (SEEDS / "gmzz.strat").read_text(encoding="utf-8")
    report, _, _ = _check(text.replace("way_out = gate_a;", "way_out = gate_b;"))
    assert report.status == "PASS"          # gate_b is raised too
    _, codes, _ = _check(text.replace('set_mode(gate_a, "raised")', 'set_mode(gate_a, "lowered")'))
    assert TRAP_CODES <= codes              # lowering the bound gate closes nothing
