from __future__ import annotations

import re
from collections import defaultdict
from typing import Any, Iterable

from .models import AuditResult, Finding, SafeChange


_SPACE_RE = re.compile(r"\s+")
_RANGE_CODE_RE = re.compile(r"(\d+)\s*-\s*(\d+)\s*cm\s*/\s*(\d+)\s*cm", re.IGNORECASE)


def normalize_text(value: Any) -> Any:
    if not isinstance(value, str):
        return value
    return _SPACE_RE.sub(" ", value).strip()


def _is_empty(value: Any) -> bool:
    return value is None or (isinstance(value, str) and not value.strip())


def _text_key(value: Any) -> str | None:
    if _is_empty(value):
        return None
    return str(normalize_text(value)).casefold()


def _display_ean(value: Any) -> str | None:
    if _is_empty(value):
        return None
    text = str(value).strip()
    if text.endswith(".0"):
        text = text[:-2]
    return text


def analyze_rows(
    headers: list[str],
    data_rows: list[list[Any]],
    contract: dict[str, Any],
    *,
    source_sheet: str | None = None,
    workbook_sheet_names: Iterable[str] = (),
    helper_rows: list[list[Any]] | None = None,
) -> AuditResult:
    source_sheet = source_sheet or contract["source_sheet"]
    findings: list[Finding] = []
    safe_changes: list[SafeChange] = []
    header_index = {name: idx for idx, name in enumerate(headers)}

    missing_columns = [name for name in contract["required_columns"] if name not in header_index]
    for name in missing_columns:
        findings.append(Finding(
            "BLOCKER", "MISSING_COLUMN", 1, name,
            f"Brak wymaganej kolumny: {name}",
            suggested_action="Uzupełnij lub jednoznacznie zmapuj kolumnę przed wykonaniem apply.",
        ))

    result = AuditResult(source_sheet, headers, len(data_rows), findings, safe_changes)
    if missing_columns:
        result.metrics = {"records": len(data_rows), "blockers": len(findings)}
        return result

    rows = [dict(zip(headers, row)) for row in data_rows]

    for excel_row, row in enumerate(rows, start=2):
        for field in contract.get("required_value_columns", []):
            if _is_empty(row.get(field)):
                findings.append(Finding(
                    "BLOCKER", "MISSING_REQUIRED_VALUE", excel_row, field,
                    f"Brak wymaganej wartości w polu „{field}”.",
                    current_value=row.get(field),
                    suggested_action="Uzupełnij wartość na podstawie źródła prawdy.",
                ))

        for field, value in row.items():
            normalized = normalize_text(value)
            if isinstance(value, str) and normalized != value:
                safe_changes.append(SafeChange(
                    excel_row, field, value, normalized,
                    "Usunięcie zewnętrznych lub powtarzających się białych znaków.",
                ))

        price = row.get("Cena netto")
        if isinstance(price, (int, float)) and not isinstance(price, bool) and price <= 0:
            findings.append(Finding(
                "ERROR", "NON_POSITIVE_PRICE", excel_row, "Cena netto",
                "Cena netto jest równa zero lub jest ujemna.", price,
                suggested_action="Zweryfikuj cenę w systemie źródłowym; agent nie zmienia jej automatycznie.",
            ))

        ean = _display_ean(row.get("EAN"))
        if ean and not re.fullmatch(rf"\d{{{contract['ean']['digits']}}}", ean):
            findings.append(Finding(
                "ERROR", "INVALID_EAN_LENGTH", excel_row, "EAN",
                f"EAN nie ma {contract['ean']['digits']} cyfr.", ean,
                suggested_action="Sprawdź EAN na opakowaniu lub w systemie źródłowym.",
            ))

        variant = normalize_text(row.get("Rozmiar / wariant"))
        if isinstance(variant, str):
            match = _RANGE_CODE_RE.search(variant)
            if match and match.group(3) == f"{match.group(1)}{match.group(2)}":
                findings.append(Finding(
                    "WARNING", "SUSPECT_VARIANT_CODE", excel_row, "Rozmiar / wariant",
                    "Pole wygląda jak połączenie właściwego zakresu z technicznym kodem rozmiaru.",
                    variant,
                    suggested_action="Potwierdź, czy druga wartość jest kodem SKU; nie usuwaj jej automatycznie.",
                ))

        stock = row.get("Stan")
        active = row.get("Aktywny")
        if active is True and isinstance(stock, (int, float)) and stock == 0:
            findings.append(Finding(
                "WARNING", "ACTIVE_WITH_ZERO_STOCK", excel_row, "Stan",
                "Produkt aktywny ma zerowy stan.", stock,
                suggested_action="Sprawdź, czy produkt ma być aktywny pomimo braku stanu.",
            ))
        if active is False and isinstance(stock, (int, float)) and stock > 0:
            findings.append(Finding(
                "INFO", "INACTIVE_WITH_STOCK", excel_row, "Aktywny",
                "Produkt nieaktywny ma dodatni stan magazynowy.", active,
                suggested_action="Sprawdź przyczynę dezaktywacji; nie aktywuj automatycznie.",
            ))

        if _is_empty(row.get("Waga kg")) and row.get("Podkategoria") not in set(contract.get("weight_optional_subcategories", [])):
            findings.append(Finding(
                "ERROR", "MISSING_WEIGHT", excel_row, "Waga kg",
                "Brak wagi w kategorii, dla której kontrakt jej nie wyłącza.",
                suggested_action="Uzupełnij zweryfikowaną wagę wysyłkową.",
            ))

    for field in contract.get("unique_columns", []):
        groups: dict[str, list[int]] = defaultdict(list)
        for excel_row, row in enumerate(rows, start=2):
            key = _text_key(row.get(field))
            if key:
                groups[key].append(excel_row)
        for related in groups.values():
            if len(related) > 1:
                for excel_row in related:
                    findings.append(Finding(
                        "BLOCKER", f"DUPLICATE_{field.upper().replace(' ', '_')}", excel_row, field,
                        f"Wartość w unikalnym polu „{field}” występuje wielokrotnie.",
                        rows[excel_row - 2].get(field), tuple(related),
                        "Rozstrzygnij duplikat przed importem.",
                    ))

    for field in contract.get("review_duplicate_columns", []):
        groups: dict[str, list[int]] = defaultdict(list)
        for excel_row, row in enumerate(rows, start=2):
            value = _display_ean(row.get(field)) if field == "EAN" else row.get(field)
            key = _text_key(value)
            if key:
                groups[key].append(excel_row)
        for related in groups.values():
            if len(related) > 1:
                for excel_row in related:
                    findings.append(Finding(
                        "REVIEW", f"DUPLICATE_{field.upper().replace(' ', '_')}", excel_row, field,
                        f"Wartość w polu „{field}” występuje w kilku rekordach.",
                        rows[excel_row - 2].get(field), tuple(related),
                        "Porównaj wariant, historię zamówień i dane źródłowe; nie scalaj automatycznie.",
                    ))

    helper_text = "\n".join(
        str(cell) for row in (helper_rows or []) for cell in row if isinstance(cell, str)
    )
    actual_sheets = set(workbook_sheet_names)
    mentioned = set(re.findall(r"\b(?:PRODUKTY|WIDOK_[A-ZĄĆĘŁŃÓŚŹŻ_]+|ARCHIWUM_DANYCH|MIGRACJA_SKU|SŁOWNIK_SKU|DUPLIKATY|PODSUMOWANIE_DUPLIKATÓW|AUDYT_SKU|AUDYT_WAG)\b", helper_text))
    missing_mentioned = sorted(name for name in mentioned if name not in actual_sheets)
    if missing_mentioned:
        findings.append(Finding(
            "WARNING", "DOCUMENTATION_SHEET_MISMATCH", None, None,
            "Dokumentacja pomocnicza odwołuje się do arkuszy, których nie ma w skoroszycie.",
            ", ".join(missing_mentioned),
            suggested_action="Zaktualizuj instrukcję lub przywróć brakujące arkusze.",
        ))

    severity_counts: dict[str, int] = defaultdict(int)
    code_counts: dict[str, int] = defaultdict(int)
    for item in findings:
        severity_counts[item.severity] += 1
        code_counts[item.code] += 1
    result.metrics = {
        "records": len(rows),
        "findings": len(findings),
        "safe_changes": len(safe_changes),
        "severity_counts": dict(sorted(severity_counts.items())),
        "code_counts": dict(sorted(code_counts.items())),
        "unique_product_ids": len({_text_key(row.get("ID produktu")) for row in rows}),
        "unique_skus": len({_text_key(row.get("SKU")) for row in rows}),
    }
    return result


def apply_safe_changes(headers: list[str], data_rows: list[list[Any]]) -> list[list[Any]]:
    output: list[list[Any]] = []
    for row in data_rows:
        output.append([normalize_text(value) for value in row])
    return output
