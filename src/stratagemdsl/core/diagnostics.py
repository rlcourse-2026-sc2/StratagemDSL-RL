from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass
class Diagnostic:
    code: str
    message: str
    severity: str = "error"  # error | warning

    def __str__(self) -> str:
        return f"[{self.severity.upper()}] {self.code}: {self.message}"


class DiagnosticBag:
    def __init__(self) -> None:
        self.items: list[Diagnostic] = []

    def error(self, code: str, message: str) -> None:
        self.items.append(Diagnostic(code, message, "error"))

    def warn(self, code: str, message: str) -> None:
        self.items.append(Diagnostic(code, message, "warning"))

    @property
    def has_errors(self) -> bool:
        return any(d.severity == "error" for d in self.items)

    def extend(self, items: Iterable[Diagnostic]) -> None:
        self.items.extend(items)
