"""Regenerate tests/golden/* from the current code.

Run only after deciding that a change in diagnostics or Galaxy output is
intended; review the resulting git diff before committing it.

    python tools/update_golden.py            # net diagnostics + Galaxy hashes
    python tools/update_golden.py --classic  # also rewrite the v0.5 diagnostics baseline

diagnostics.json is the frozen v0.5 checker baseline (every code except the
v0.6 N0xx net codes); net_diagnostics.json records the net analysis.
"""
import hashlib
import json
import sys

from stratagemdsl.backend.galaxy import GalaxyLowerer
from stratagemdsl.frontend import parse_file
from stratagemdsl.paths import REPO_ROOT
from stratagemdsl.semantics import Validator

classic_mode = "--classic" in sys.argv
golden = REPO_ROOT / "tests/golden"
classic = json.loads((golden / "diagnostics.json").read_text(encoding="utf-8"))
galaxy, net = {}, {}
for path in sorted(p for d in ("examples", "tests/fixtures") for p in (REPO_ROOT / d).rglob("*.strat")):
    rel = path.relative_to(REPO_ROOT).as_posix()
    strategy = parse_file(path, "lark")
    entry_classic, entry_net = {}, {}
    for profile, strict in (("loose", False), ("strict", True)):
        items = Validator(strategy, strict_sc2=strict).validate().items
        entry_classic[profile] = [str(d) for d in items if not d.code.startswith("N0")]
        entry_net[profile] = [str(d) for d in items if d.code.startswith("N0")]
    if classic_mode or rel not in classic:
        classic[rel] = entry_classic
    if any(entry_net.values()):
        net[rel] = entry_net
    try:
        galaxy[rel] = hashlib.sha256(GalaxyLowerer(strategy).emit().encode("utf-8")).hexdigest()
    except Exception as exc:
        galaxy[rel] = f"lowering_error: {type(exc).__name__}: {exc}"
for name, data in (("galaxy_sha256.json", galaxy), ("net_diagnostics.json", net), ("diagnostics.json", classic)):
    (golden / name).write_text(json.dumps(data, indent=1, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
print(f"{len(galaxy)} sources recorded; {len(net)} with net findings")
