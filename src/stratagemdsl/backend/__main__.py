"""Debug layer 4: python -m stratagemdsl.backend FILE [-o OUT.galaxy] [--transitions] [--intents]

Lowers without validating first, so a lowering bug can be reproduced even on
input the checker would reject. Prints Galaxy to stdout unless -o is given.
"""
import argparse
import json
import sys
from pathlib import Path

from stratagemdsl.backend.galaxy import GalaxyLowerer, LoweringError
from stratagemdsl.backend.intents import agent_intents_json
from stratagemdsl.frontend import parse_file


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="python -m stratagemdsl.backend", description=__doc__)
    ap.add_argument("source")
    ap.add_argument("-o", "--output", help="write MapScript Galaxy here")
    ap.add_argument("--transitions", action="store_true", help="print how each transition was lowered")
    ap.add_argument("--intents", action="store_true", help="print the allied agent-intent sidecar")
    ap.add_argument("--oracle", action="store_true",
                    help="also emit allied attack/move/cast orders into the Galaxy program")
    args = ap.parse_args(argv)
    strategy = parse_file(args.source, "lark")
    try:
        lowerer = GalaxyLowerer(strategy, oracle=args.oracle)
        galaxy = lowerer.emit()
    except LoweringError as exc:
        print(f"[LOWERING ERROR] {exc}")
        return 1
    if args.output:
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.output).write_text(galaxy, encoding="utf-8")
        print(f"Galaxy: {args.output} ({len(galaxy.splitlines())} lines)")
    elif not (args.transitions or args.intents):
        print(galaxy)
    if args.transitions:
        print(json.dumps(lowerer.transition_kinds, ensure_ascii=False, indent=2))
    if args.intents:
        print(agent_intents_json(strategy))
    for note in sorted(set(lowerer.notes)):
        print(f"[NOTE] {note}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
