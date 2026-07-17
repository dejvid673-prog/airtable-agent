from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .models import AuditResult


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")


def audit_markdown(result: AuditResult, input_sha256: str) -> str:
    counts = result.metrics.get("severity_counts", {})
    lines = [
        "# Raport audytu skoroszytu",
        "",
        f"- Arkusz źródłowy: `{result.source_sheet}`",
        f"- Rekordy: **{result.row_count}**",
        f"- SHA-256 wejścia: `{input_sha256}`",
        f"- Wszystkie ustalenia: **{len(result.findings)}**",
        f"- Bezpieczne normalizacje: **{len(result.safe_changes)}**",
        "",
        "## Ustalenia według ważności",
        "",
    ]
    for severity in ("BLOCKER", "ERROR", "WARNING", "REVIEW", "INFO"):
        lines.append(f"- {severity}: **{counts.get(severity, 0)}**")
    lines.extend(["", "## Zasada wykonania", "", "Agent nie usuwa ani nie scala rekordów. Niepewne wartości pozostają bez zmian i trafiają do `DO_WERYFIKACJI`."])
    return "\n".join(lines) + "\n"


def plan_markdown(result: AuditResult) -> str:
    return "\n".join([
        "# Plan zmian",
        "",
        "## Wykonywane automatycznie",
        "",
        f"1. Utworzenie `EXPORT_GOTOWY` z zachowaniem {result.row_count} rekordów.",
        f"2. Zastosowanie {len(result.safe_changes)} bezpiecznych normalizacji białych znaków.",
        "3. Utworzenie arkuszy `AUDYT_AGENTA`, `DO_WERYFIKACJI` i `PLAN_ZMIAN`.",
        "4. Zachowanie wszystkich arkuszy wejściowych bez zmian.",
        "",
        "## Niewykonywane automatycznie",
        "",
        "- usuwanie lub scalanie rekordów;",
        "- zmiana SKU, EAN, cen, kategorii, stanów, aktywności i wag;",
        "- poprawianie wartości, których nie można jednoznacznie wyprowadzić z danych.",
        "",
    ])
