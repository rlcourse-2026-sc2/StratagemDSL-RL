from __future__ import annotations

from stratagemdsl.semantics.patterns.checker import PatternCheckReport


def format_pattern_report(report: PatternCheckReport) -> str:
    if not report.pattern:
        return "No strategic pattern declared."
    lines = [f"Pattern: {report.pattern}", f"Status : {report.status}"]
    if report.status == "NOT CHECKED":
        lines.append(f"Reason : {report.reason}; no causal obligation was checked.")
    else:
        lines.append("Evidence: static plan witnesses; an issued order or inferred fact does not prove a runtime effect.")
    if report.witnesses:
        lines.append("Witnesses:")
        for w in report.witnesses:
            lines.append(f"  [{w.code}]")
            for i, f in enumerate(w.path):
                prefix = "    -> " if i else "       "
                lines.append(prefix + f.short() + f" [{f.evidence}]")
    if report.diagnostics:
        lines.append("Diagnostics:")
        for d in report.diagnostics:
            lines.append("  " + str(d))
    return "\n".join(lines)
