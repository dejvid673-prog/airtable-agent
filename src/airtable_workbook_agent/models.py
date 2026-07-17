from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class Finding:
    severity: str
    code: str
    row: int | None
    field: str | None
    message: str
    current_value: Any = None
    related_rows: tuple[int, ...] = ()
    suggested_action: str = "Przekaż do decyzji człowieka."

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["related_rows"] = list(self.related_rows)
        return value


@dataclass(frozen=True)
class SafeChange:
    row: int
    field: str
    before: Any
    after: Any
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class AuditResult:
    source_sheet: str
    headers: list[str]
    row_count: int
    findings: list[Finding] = field(default_factory=list)
    safe_changes: list[SafeChange] = field(default_factory=list)
    metrics: dict[str, Any] = field(default_factory=dict)

    @property
    def blockers(self) -> list[Finding]:
        return [item for item in self.findings if item.severity == "BLOCKER"]

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_sheet": self.source_sheet,
            "headers": self.headers,
            "row_count": self.row_count,
            "metrics": self.metrics,
            "safe_changes": [item.to_dict() for item in self.safe_changes],
            "findings": [item.to_dict() for item in self.findings],
        }
