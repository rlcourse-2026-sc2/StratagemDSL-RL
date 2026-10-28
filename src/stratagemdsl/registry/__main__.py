"""Debug layer 2: python -m stratagemdsl.registry [NAME ...] [--namespace function|event|action]

Without names, lists every registered API; with names, shows signatures,
literal vocabularies, event contexts and the exported contract.
"""
import argparse
import sys

from stratagemdsl.registry import extensions as api
from stratagemdsl.registry.contracts import REGISTRY, contracts


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="python -m stratagemdsl.registry", description=__doc__)
    ap.add_argument("names", nargs="*")
    ap.add_argument("--namespace", choices=["function", "event", "action"])
    args = ap.parse_args(argv)
    if not args.names:
        for spec in contracts(args.namespace):
            sigs = " | ".join(f"({', '.join(s.args)}) -> {s.returns}" for s in spec.signatures)
            print(f"{spec.namespace:8} {spec.name:28} {spec.backend:15} {sigs}")
        return 0
    status = 0
    for name in args.names:
        found = [spec for (ns, n), spec in REGISTRY.items() if n == name]
        if not found:
            print(f"{name}: not registered")
            status = 1
        for spec in found:
            print(f"{spec.namespace} {spec.name}  backend={spec.backend}  actor={spec.actor}")
            for s in spec.signatures:
                print(f"  ({', '.join(s.args)}) -> {s.returns}")
            for (n, i), vocab in sorted(api.VOCAB.items()):
                if n == name:
                    words = vocab if isinstance(vocab, str) else sorted(vocab)
                    print(f"  arg {i + 1} vocabulary: {words}")
            if name in api.CTX:
                print(f"  only inside events: {sorted(api.CTX[name])}")
            if name in api.ACTS:
                print(f"  action scope: {api.ACTS[name][1]}")
            print(f"  galaxy: {spec.galaxy}")
    return status


if __name__ == "__main__":
    sys.exit(main())
