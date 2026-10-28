"""Debug layer 3: python -m stratagemdsl.semantics FILE [--strict] [--pattern-report]

Runs only the static checks. ``--strict`` adds the SC2 executability rules but
not the backend dry run (that probe is wired in by stratagemdsl.pipeline).
"""
import argparse
import sys

from stratagemdsl.frontend import parse_file
from stratagemdsl.semantics import Validator
from stratagemdsl.semantics.patterns.report import format_pattern_report


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="python -m stratagemdsl.semantics", description=__doc__)
    ap.add_argument("source")
    ap.add_argument("--strict", action="store_true", help="enable strict SC2 executability rules")
    ap.add_argument("--pattern-report", action="store_true")
    args = ap.parse_args(argv)
    validator = Validator(parse_file(args.source, "lark"), strict_sc2=args.strict)
    bag = validator.validate()
    for d in bag.items:
        print(d)
    if not bag.items:
        print("[OK] no diagnostics")
    if args.pattern_report:
        print()
        print(format_pattern_report(validator.pattern_report))
    return 1 if bag.has_errors else 0


if __name__ == "__main__":
    sys.exit(main())
