"""Debug layer 1: python -m stratagemdsl.frontend FILE [--frontend lark|antlr|auto] [--json] [--compare]"""
import argparse
import json
import sys

from stratagemdsl.frontend import FRONTENDS, parse_file


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="python -m stratagemdsl.frontend", description=__doc__)
    ap.add_argument("source")
    ap.add_argument("--frontend", choices=FRONTENDS, default="lark")
    ap.add_argument("--json", action="store_true", help="print the full AST as JSON")
    ap.add_argument("--compare", action="store_true", help="check that lark and antlr build the same AST")
    args = ap.parse_args(argv)
    strategy = parse_file(args.source, args.frontend)
    if args.compare:
        same = parse_file(args.source, "lark").to_dict() == parse_file(args.source, "antlr").to_dict()
        print(f"frontends agree: {same}")
        if not same:
            return 1
    if args.json:
        print(json.dumps(strategy.to_dict(), ensure_ascii=False, indent=2))
    else:
        print(f"{strategy.name}: {len(strategy.world)} entities, {len(strategy.plan.nodes)} nodes, "
              f"{len(strategy.plan.transitions)} transitions, start={strategy.plan.start}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
