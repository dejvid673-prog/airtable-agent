from __future__ import annotations

from pathlib import Path
from typing import Any

from .contracts import load_workbook_contract
from .product_transform import transform_rows
from .reporting import write_json, write_markdown
from .xlsx_backend import read_sheet, verify_result_workbook, write_result_workbook


def prepare_workbook(
    input_path: str | Path,
    output_path: str | Path,
    run_dir: str | Path,
    contract_path: str | Path | None = None,
) -> dict[str, Any]:
    contract = load_workbook_contract(contract_path)
    headers, rows, sheets = read_sheet(input_path, contract["source_sheet"])
    result = transform_rows(headers, rows, contract)
    blockers = [item for item in result.findings if item.severity == "BLOCKER"]
    run_path = Path(run_dir)
    run_path.mkdir(parents=True, exist_ok=True)
    write_json(run_path / "audit.json", {
        "source_sheet": contract["source_sheet"],
        "source_sheets": sheets,
        "headers": headers,
        "metrics": result.metrics,
        "findings": [item.to_dict() for item in result.findings],
    })
    write_markdown(run_path / "audit.md", "Audyt skoroszytu", [
        ("Podsumowanie", [
            f"- Rekordy: **{len(rows)}**",
            f"- Ustalenia: **{len(result.findings)}**",
            f"- Blockery: **{len(blockers)}**",
        ]),
        ("Zasady", [
            "- Oryginalny plik nie jest nadpisywany.",
            "- Kategorie są mapowane wyłącznie według jawnego kontraktu.",
            "- Ceny, stany, aktywność i EAN nie są zmieniane.",
        ]),
    ])
    if blockers:
        write_json(run_path / "execution.json", {"status": "blocked", "blockers": [item.to_dict() for item in blockers]})
        raise RuntimeError(f"Przetwarzanie zablokowane: {len(blockers)} problemów BLOCKER.")
    execution = write_result_workbook(input_path, output_path, headers, rows, result, contract)
    payload = {
        "status": "completed",
        "input": str(input_path),
        "output": str(output_path),
        "metrics": result.metrics,
        **execution,
    }
    write_json(run_path / "execution.json", payload)
    write_json(run_path / "verification.json", execution["verification"])
    return payload


def verify_workbook(input_path: str | Path, output_path: str | Path, contract_path: str | Path | None = None) -> dict[str, Any]:
    return verify_result_workbook(input_path, output_path, load_workbook_contract(contract_path))
