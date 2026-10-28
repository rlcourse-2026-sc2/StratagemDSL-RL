from __future__ import annotations

import difflib
from dataclasses import dataclass, field

from stratagemdsl.registry.builtins import is_subtype
from stratagemdsl.core.diagnostics import Diagnostic, DiagnosticBag
from stratagemdsl.semantics.patterns.library import PatternDef, FactPattern, get_pattern, known_pattern_names
from stratagemdsl.semantics.patterns.facts import FactExtractor, StrategicFact


@dataclass
class ObligationWitness:
    code: str
    source: StrategicFact
    target: StrategicFact
    path: list[StrategicFact]


@dataclass
class PatternCheckReport:
    """`passed` is False only when an obligation or a role binding failed.
    `checked` says whether the obligations were checked at all: an unbound
    pattern, or a pattern with no causal definition, passes unchecked."""
    pattern: str
    passed: bool
    witnesses: list[ObligationWitness] = field(default_factory=list)
    diagnostics: list[Diagnostic] = field(default_factory=list)
    checked: bool = False
    reason: str = ""

    @property
    def status(self) -> str:
        if not self.pattern:
            return "NONE"
        if not self.passed:
            return "FAIL"
        return "PASS" if self.checked else "NOT CHECKED"


class PatternChecker:
    def __init__(self, strategy, symbol_types: dict[str, str]) -> None:
        self.s = strategy
        self.symbol_types = symbol_types
        self.d = DiagnosticBag()
        self.witnesses: list[ObligationWitness] = []

    def check(self) -> PatternCheckReport:
        name = self.s.intent.pattern if self.s.intent else None
        if not name:
            return PatternCheckReport("", True)
        p = get_pattern(name)
        if p is None:
            if name in known_pattern_names():
                # Used by the corpus but not yet given a causal definition; some
                # of these keep legacy lint rules in the validator.
                return PatternCheckReport(name, True, reason=f"pattern '{name}' has no causal definition yet")
            close = difflib.get_close_matches(name.lower(), {k.lower(): k for k in known_pattern_names()}, n=1, cutoff=0.6)
            hint = ""
            if close:
                hint = " Did you mean '" + {k.lower(): k for k in known_pattern_names()}[close[0]] + "'?"
            self.d.warn(
                "C096_PATTERN_UNKNOWN",
                f"unknown pattern '{name}'; no pattern check runs.{hint} "
                f"Known patterns: {', '.join(sorted(known_pattern_names()))}",
            )
            return PatternCheckReport(name, True, diagnostics=self.d.items, reason=f"unknown pattern '{name}'")

        bindings = self.s.intent.pattern_bindings
        if not bindings:
            self.d.warn(
                "C090_PATTERN_UNBOUND",
                f"pattern '{name}' uses legacy unbound syntax; causal proof skipped. Add explicit role bindings.",
            )
            return PatternCheckReport(name, True, diagnostics=self.d.items, reason="no role bindings")

        self._check_bindings(p, bindings)
        if self.d.has_errors:
            return PatternCheckReport(name, False, diagnostics=self.d.items, checked=True)

        g = FactExtractor(self.s).extract()
        for ob in p.obligations:
            src_pat = self._instantiate(ob.source, bindings)
            dst_pat = self._instantiate(ob.target, bindings)
            srcs = g.matching(src_pat.kind, src_pat.args)
            dsts = g.matching(dst_pat.kind, dst_pat.args)
            best = None
            for a in srcs:
                for b in dsts:
                    path = g.find_path(a, b)
                    if path is not None:
                        best = ObligationWitness(ob.code, a, b, path)
                        break
                if best:
                    break
            if best:
                self.witnesses.append(best)
            else:
                detail = []
                if not srcs:
                    detail.append(f"missing source fact {src_pat.kind}{src_pat.args}")
                if not dsts:
                    detail.append(f"missing target fact {dst_pat.kind}{dst_pat.args}")
                if srcs and dsts:
                    detail.append("source and target exist but no causal/ordered path connects them")
                self.d.error(ob.code, ob.message + (" " + "; ".join(detail) if detail else ""))

        return PatternCheckReport(name, not self.d.has_errors, self.witnesses, self.d.items, checked=True)

    def _check_bindings(self, p: PatternDef, bindings: dict[str, str]) -> None:
        expected = {r.name: r for r in p.roles}
        for role, spec in expected.items():
            if role not in bindings:
                self.d.error("C091_PATTERN_ROLE_MISSING", f"pattern '{p.name}' missing role binding '{role}'")
                continue
            entity = bindings[role]
            actual = self.symbol_types.get(entity)
            if actual is None:
                self.d.error("C092_PATTERN_ENTITY_UNKNOWN", f"pattern role '{role}' binds unknown entity '{entity}'")
            elif not is_subtype(actual, spec.type_name):
                self.d.error(
                    "C093_PATTERN_ROLE_TYPE",
                    f"pattern role '{role}' expects {spec.type_name}, got {actual} from '{entity}'",
                )
        for role in bindings:
            if role not in expected:
                self.d.error("C094_PATTERN_ROLE_UNKNOWN", f"pattern '{p.name}' has no role '{role}'")
        for a, b in p.distinct_roles:
            if bindings.get(a) is not None and bindings.get(a) == bindings.get(b):
                self.d.error("C095_PATTERN_DISTINCT", f"pattern '{p.name}' requires roles '{a}' and '{b}' to bind distinct entities")

    @staticmethod
    def _instantiate(fp: FactPattern, bindings: dict[str, str]) -> FactPattern:
        args = tuple(bindings.get(x[1:], x) if x.startswith("$") else x for x in fp.args)
        return FactPattern(fp.kind, args)
