"""Regression coverage for map-safe per-strategy memory ownership.

These checks exercise lowering and reset plans. They do not simulate the SC2
engine or assert runtime event ordering.
"""

import re
from types import SimpleNamespace

from stratagemdsl.backend.galaxy import extensions as ext
from stratagemdsl.core.model import CallExpr, NameExpr, NumberExpr, StringExpr


def lowerer(name="lesson"):
    lo = SimpleNamespace(s=SimpleNamespace(name=name))
    lo.ext_state = ext.ExtensionState(lo)
    lo._group = lambda name: "gv_" + name
    return lo


def call(name, *args):
    return CallExpr(name, list(args))


def test_reset_removes_owned_keys_and_preserves_other_map_data():
    lo = lowerer()
    lo.ext_state.memory_key("threat")
    lo.ext_state.memory_key("wave", kind="snapshot_size")
    other = lowerer("independent_lesson").ext_state.memory_key("threat")
    external = {"native_campaign_score": 123, other: 5}
    data = {**external, **{name: 99 for name in lo.ext_state.memory_keys}}
    commands = ext.spawn_lines(lo)
    assert all("DataTableClear" not in line for line in commands)
    for command in commands:
        match = re.fullmatch(r'    DataTableValueRemove\(true, "([^"]+)"\);', command)
        assert match, command
        data.pop(match.group(1), None)
    assert data == external


def test_snapshot_metadata_cannot_collide_with_a_user_key():
    lo = lowerer()
    snap = call("snapshot", StringExpr("wave"), NameExpr("fighters"))
    lines = ext.LOWER_ACT["snapshot"](lo, snap, "    ")
    metadata = ext.snapshot_size_key(lo, snap)
    user = call("tally", StringExpr("wave#n"), NumberExpr(1))
    tally_lines = ext.LOWER_ACT["tally"](lo, user, "    ")
    assert metadata in lines[1]
    assert metadata not in tally_lines[0]
    assert ext.key(lo, user) != metadata


def test_forgetting_a_snapshot_also_discards_its_baseline_count():
    lo = lowerer()
    forget = call("forget", StringExpr("wave"))
    lines = ext.LOWER_ACT["forget"](lo, forget, "    ")
    assert lines == [
        f"    DataTableValueRemove(true, {ext.key(lo, forget)});",
        f"    DataTableValueRemove(true, {ext.snapshot_size_key(lo, forget)});",
    ]


def test_strategy_names_unicode_and_delimiters_remain_distinct():
    one, two = lowerer("one"), lowerer("two")
    keys = {one.ext_state.memory_key("wave"), one.ext_state.memory_key("wave#n"),
            one.ext_state.memory_key("wave", kind="snapshot_size"),
            one.ext_state.memory_key("敌军:位置"), two.ext_state.memory_key("wave")}
    assert len(keys) == 5
    assert all('"' not in key and "\\" not in key for key in keys)
