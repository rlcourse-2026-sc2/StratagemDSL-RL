"""Debug layer 3 (net): python -m stratagemdsl.net FILE [--pnml OUT] [--plain] [--cross-check] [--trace]

Builds the plan's Petri net and prints its places, transitions and analysis.
"""
import argparse
import json
import sys

from stratagemdsl.frontend import parse_file
from stratagemdsl.frontend.unparse import print_arcs
from stratagemdsl.net import analyze, build_net
from stratagemdsl.net.pnml import to_pnml


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="python -m stratagemdsl.net", description=__doc__)
    ap.add_argument("source")
    ap.add_argument("--pnml")
    ap.add_argument("--plain", action="store_true")
    ap.add_argument("--cross-check", action="store_true")
    ap.add_argument("--witness", action="store_true", help="print a dispatch sequence that fires each transition")
    a = ap.parse_args(argv)
    net = build_net(parse_file(a.source, "lark"))
    print(f"net {net.name}: {net.stats()}")
    for p in net.places.values():
        print(f"  place {p.id:32} kind={p.kind:13} m0={p.initial} cap={p.capacity} once={p.once}"
              + (f" terminal={p.terminal}" if p.terminal else ""))
    for t in net.transitions:
        print(f"  trans {t.id:32} {t.dispatch:9} rank={t.rank} {print_arcs(t.inputs)} -> {print_arcs(t.outputs)}")
    report = analyze(net)
    print(json.dumps(report.summary(), ensure_ascii=False, indent=2, default=str))
    if a.witness:
        for tid, path in sorted(report.witnesses().items()):
            print(f"  {tid}: " + " ; ".join(f"{k[0]}{'' if k[0] == 'poll' else ':' + str(k[1][0]) if len(k) > 1 else ''}{list(sel)}" for k, sel in path))
    if a.cross_check:
        from stratagemdsl.net.snakes_bridge import cross_check
        print("SNAKES cross-check:", cross_check(net))
    if a.pnml:
        open(a.pnml, "w", encoding="utf-8").write(to_pnml(net, plain=a.plain))
    return 0


if __name__ == "__main__":
    sys.exit(main())
