from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from .contracts import load_contract
from .models import AuditResult
from .reporting import audit_markdown, plan_markdown, write_json
from .rules import analyze_rows, apply_safe_changes


GENERATED_SHEETS = ("EXPORT_GOTOWY", "AUDYT_AGENTA", "DO_WERYFIKACJI", "PLAN_ZMIAN")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _artifact_imports():
    try:
        from artifact_tool import Blob, SpreadsheetFile  # type: ignore
    except ImportError as exc:
        raise RuntimeError(
            "Brak artifact_tool. Uruchom agenta w środowisku OpenAI Artifact Runtime."
        ) from exc
    return Blob, SpreadsheetFile


def _read_workbook(input_path: Path, contract: dict[str, Any]):
    Blob, SpreadsheetFile = _artifact_imports()
    workbook = SpreadsheetFile.import_xlsx(Blob.load(str(input_path)))
    source_name = contract["source_sheet"]
    source = workbook.worksheets.get_item(source_name)
    source_range = source.get_range("A1").get_current_region()
    values = source_range.values
    if not values:
        raise ValueError(f"Arkusz {source_name} jest pusty.")
    sheet_names = [workbook.worksheets.get_sheet_name_by_index(i) for i in range(workbook.worksheets.get_sheet_count())]
    helper_rows: list[list[Any]] = []
    if "DANE_POMOCNICZE" in sheet_names:
        helper = workbook.worksheets.get_item("DANE_POMOCNICZE")
        helper_rows = helper.get_range("A1").get_current_region().values
    return workbook, values[0], values[1:], sheet_names, helper_rows, SpreadsheetFile


def analyze(input_path: Path, run_dir: Path, contract_path: Path | None = None) -> AuditResult:
    contract = load_contract(contract_path)
    _, headers, rows, sheet_names, helper_rows, _ = _read_workbook(input_path, contract)
    result = analyze_rows(
        headers, rows, contract,
        source_sheet=contract["source_sheet"],
        workbook_sheet_names=sheet_names,
        helper_rows=helper_rows,
    )
    run_dir.mkdir(parents=True, exist_ok=True)
    input_hash = sha256_file(input_path)
    write_json(run_dir / "audit.json", result.to_dict())
    (run_dir / "audit.md").write_text(audit_markdown(result, input_hash), encoding="utf-8")
    (run_dir / "plan.md").write_text(plan_markdown(result), encoding="utf-8")
    write_json(run_dir / "input_manifest.json", {
        "input_path": str(input_path),
        "input_sha256": input_hash,
        "source_sheet": contract["source_sheet"],
        "record_count": result.row_count,
        "headers": headers,
    })
    return result


def _clear_and_write(sheet, values: list[list[Any]]) -> None:
    current = sheet.get_range("A1").get_current_region()
    current_values = current.values
    if current_values and any(any(cell is not None for cell in row) for row in current_values):
        current.clear({"contents": True, "formats": True})
    if values:
        sheet.get_range("A1").write(values)


def _style_export(sheet, rows: int, cols: int) -> None:
    header = sheet.get_range_by_indexes(0, 0, 1, cols)
    header.format = {
        "fill": "#1F4E78",
        "font": {"bold": True, "color": "#FFFFFF"},
        "horizontal_alignment": "center",
        "vertical_alignment": "center",
        "wrap_text": True,
    }
    sheet.freeze_panes.freeze_rows(1)
    sheet.get_range_by_indexes(0, 0, max(rows, 1), cols).format.autofit_columns()
    for col, width in {0: 12, 1: 20, 2: 40, 3: 20, 4: 24, 5: 24, 6: 12, 7: 14, 8: 10, 9: 10, 10: 18}.items():
        if col < cols:
            sheet.get_range_by_indexes(0, col, max(rows, 1), 1).format.column_width = width
    if rows > 1:
        sheet.get_range_by_indexes(1, 6, rows - 1, 2).format.number_format = "0.00"
        sheet.get_range_by_indexes(1, 8, rows - 1, 1).format.number_format = "0"
        sheet.get_range_by_indexes(1, 10, rows - 1, 1).format.number_format = "@"


def apply(input_path: Path, output_path: Path, run_dir: Path, contract_path: Path | None = None) -> dict[str, Any]:
    contract = load_contract(contract_path)
    original_hash = sha256_file(input_path)
    workbook, headers, rows, sheet_names, helper_rows, SpreadsheetFile = _read_workbook(input_path, contract)
    result = analyze_rows(
        headers, rows, contract,
        source_sheet=contract["source_sheet"],
        workbook_sheet_names=sheet_names,
        helper_rows=helper_rows,
    )
    if result.blockers:
        raise RuntimeError(f"Apply zablokowany: wykryto {len(result.blockers)} problemów BLOCKER.")

    prepared = [headers] + apply_safe_changes(headers, rows)
    export_sheet = workbook.worksheets.get_or_add(contract["prepared_sheet"])
    _clear_and_write(export_sheet, prepared)
    _style_export(export_sheet, len(prepared), len(headers))

    audit_values = [
        ["AUDYT AGENTA", "Wartość"],
        ["Wersja kontraktu", contract["contract_version"]],
        ["Arkusz źródłowy", contract["source_sheet"]],
        ["Liczba rekordów", result.row_count],
        ["Wszystkie ustalenia", len(result.findings)],
        ["Bezpieczne normalizacje", len(result.safe_changes)],
        ["SHA-256 wejścia", original_hash],
        ["Zasada", "Arkusz źródłowy pozostawiono bez zmian."],
    ]
    for severity, count in result.metrics.get("severity_counts", {}).items():
        audit_values.append([f"Ustalenia {severity}", count])
    audit_sheet = workbook.worksheets.get_or_add("AUDYT_AGENTA")
    _clear_and_write(audit_sheet, audit_values)
    audit_sheet.get_range("A1:B1").format = {"fill": "#1F4E78", "font": {"bold": True, "color": "#FFFFFF"}}
    audit_sheet.get_range_by_indexes(0, 0, len(audit_values), 2).format.autofit_columns()

    source_rows = {index: dict(zip(headers, row)) for index, row in enumerate(rows, start=2)}
    review_header = ["Ważność", "Kod", "Wiersz źródłowy", "ID produktu", "SKU", "Nazwa produktu", "Pole", "Bieżąca wartość", "Opis", "Zalecenie", "Powiązane wiersze"]
    review_values = [review_header]
    order = {"BLOCKER": 0, "ERROR": 1, "WARNING": 2, "REVIEW": 3, "INFO": 4}
    for item in sorted(result.findings, key=lambda x: (order.get(x.severity, 9), x.code, x.row or 0)):
        row = source_rows.get(item.row or -1, {})
        review_values.append([
            item.severity, item.code, item.row,
            row.get("ID produktu"), row.get("SKU"), row.get("Nazwa produktu"),
            item.field, str(item.current_value) if item.current_value is not None else None,
            item.message, item.suggested_action,
            ", ".join(str(v) for v in item.related_rows),
        ])
    review_sheet = workbook.worksheets.get_or_add("DO_WERYFIKACJI")
    _clear_and_write(review_sheet, review_values)
    review_sheet.get_range("A1:K1").format = {"fill": "#9C0006", "font": {"bold": True, "color": "#FFFFFF"}, "wrap_text": True}
    review_sheet.freeze_panes.freeze_rows(1)
    review_sheet.get_range_by_indexes(0, 0, len(review_values), 11).format.autofit_columns()
    for col, width in {5: 40, 7: 24, 8: 44, 9: 44}.items():
        review_sheet.get_range_by_indexes(0, col, max(len(review_values), 1), 1).format.column_width = width
        review_sheet.get_range_by_indexes(0, col, max(len(review_values), 1), 1).format.wrap_text = True

    plan_values = [
        ["Typ", "Operacja", "Status", "Uzasadnienie"],
        ["Automatyczna", "Utworzenie EXPORT_GOTOWY", "WYKONANO", "Nie zmienia arkusza źródłowego."],
        ["Automatyczna", "Normalizacja białych znaków", "WYKONANO", f"Zmiany: {len(result.safe_changes)}"],
        ["Kontrolna", "Usuwanie lub scalanie rekordów", "ZABLOKOWANO", "Wymaga decyzji człowieka."],
        ["Kontrolna", "Zmiana SKU/EAN/cen/kategorii/wag/stanów", "ZABLOKOWANO", "Brak jednoznacznej reguły."],
    ]
    plan_sheet = workbook.worksheets.get_or_add("PLAN_ZMIAN")
    _clear_and_write(plan_sheet, plan_values)
    plan_sheet.get_range("A1:D1").format = {"fill": "#548235", "font": {"bold": True, "color": "#FFFFFF"}}
    plan_sheet.get_range_by_indexes(0, 0, len(plan_values), 4).format.autofit_columns()
    plan_sheet.get_range_by_indexes(0, 3, len(plan_values), 1).format.column_width = 48
    plan_sheet.get_range_by_indexes(0, 3, len(plan_values), 1).format.wrap_text = True

    output_path.parent.mkdir(parents=True, exist_ok=True)
    SpreadsheetFile.export_xlsx(workbook).save(str(output_path))
    after_input_hash = sha256_file(input_path)
    if after_input_hash != original_hash:
        raise RuntimeError("Plik wejściowy został zmodyfikowany — przerwano.")

    verification = verify(input_path, output_path, contract_path)
    run_dir.mkdir(parents=True, exist_ok=True)
    write_json(run_dir / "audit.json", result.to_dict())
    write_json(run_dir / "verification.json", verification)
    write_json(run_dir / "execution.json", {
        "input": str(input_path),
        "output": str(output_path),
        "input_sha256": original_hash,
        "output_sha256": sha256_file(output_path),
        "generated_sheets": list(GENERATED_SHEETS),
        "safe_changes": len(result.safe_changes),
        "findings": len(result.findings),
        "verification": verification,
    })
    (run_dir / "audit.md").write_text(audit_markdown(result, original_hash), encoding="utf-8")
    (run_dir / "plan.md").write_text(plan_markdown(result), encoding="utf-8")
    return {"audit": result.to_dict(), "verification": verification}


def verify(input_path: Path, output_path: Path, contract_path: Path | None = None) -> dict[str, Any]:
    contract = load_contract(contract_path)
    _, input_headers, input_rows, _, _, _ = _read_workbook(input_path, contract)
    output_contract = dict(contract)
    output_contract["source_sheet"] = contract["prepared_sheet"]
    _, output_headers, output_rows, output_sheet_names, _, _ = _read_workbook(output_path, output_contract)

    input_id_idx = input_headers.index("ID produktu")
    input_sku_idx = input_headers.index("SKU")
    output_id_idx = output_headers.index("ID produktu")
    output_sku_idx = output_headers.index("SKU")
    checks = {
        "input_unchanged": True,
        "headers_equal": input_headers == output_headers,
        "row_count_equal": len(input_rows) == len(output_rows),
        "product_ids_equal": [row[input_id_idx] for row in input_rows] == [row[output_id_idx] for row in output_rows],
        "skus_equal": [row[input_sku_idx] for row in input_rows] == [row[output_sku_idx] for row in output_rows],
        "generated_sheets_present": all(name in output_sheet_names for name in GENERATED_SHEETS),
    }
    return {"passed": all(checks.values()), "checks": checks, "input_rows": len(input_rows), "output_rows": len(output_rows)}
