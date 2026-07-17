from __future__ import annotations

import json
from pathlib import Path
from typing import Any


DEFAULT_CONTRACT = Path(__file__).resolve().parents[2] / "contracts" / "product_workbook_contract.json"


def load_contract(path: str | Path | None = None) -> dict[str, Any]:
    contract_path = Path(path) if path else DEFAULT_CONTRACT
    with contract_path.open("r", encoding="utf-8") as handle:
        contract = json.load(handle)
    required = {"source_sheet", "prepared_sheet", "required_columns"}
    missing = required.difference(contract)
    if missing:
        raise ValueError(f"Kontrakt nie zawiera pól: {sorted(missing)}")
    return contract
