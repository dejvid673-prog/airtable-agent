from __future__ import annotations

import json
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_WORKBOOK_CONTRACT = PROJECT_ROOT / "contracts" / "product_workbook_contract.json"


def load_json(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_workbook_contract(path: str | Path | None = None) -> dict[str, Any]:
    contract_path = Path(path) if path else DEFAULT_WORKBOOK_CONTRACT
    contract = load_json(contract_path)
    required = {"source_sheet", "prepared_sheet", "required_columns", "category_mapping"}
    missing = required.difference(contract)
    if missing:
        raise ValueError(f"Kontrakt nie zawiera pól: {sorted(missing)}")
    return contract


def load_airtable_mapping(path: str | Path) -> dict[str, Any]:
    contract = load_json(path)
    required = {"base_id", "table_id", "source_sheet", "key", "fields"}
    missing = required.difference(contract)
    if missing:
        raise ValueError(f"Mapowanie Airtable nie zawiera pól: {sorted(missing)}")
    key = contract["key"]
    if not key.get("excel_column") or not key.get("airtable_field_id"):
        raise ValueError("Mapowanie klucza wymaga excel_column i airtable_field_id.")
    if not isinstance(contract["fields"], list) or not contract["fields"]:
        raise ValueError("Mapowanie Airtable musi zawierać co najmniej jedno pole.")
    return contract
