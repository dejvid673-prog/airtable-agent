from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable

from .airtable_cli import AirtableCLI
from .contracts import load_airtable_mapping
from .reporting import canonical_json_hash, write_json
from .xlsx_backend import read_sheet


def _walk_json(value: Any) -> Iterable[Any]:
    yield value
    if isinstance(value, dict):
        for child in value.values():
            yield from _walk_json(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk_json(child)


def _extract_records(payload: Any) -> list[dict[str, Any]]:
    candidates: list[list[dict[str, Any]]] = []
    for node in _walk_json(payload):
        if isinstance(node, dict) and isinstance(node.get("records"), list):
            records = [item for item in node["records"] if isinstance(item, dict)]
            if records:
                candidates.append(records)
        elif isinstance(node, list) and node and all(isinstance(item, dict) for item in node):
            if any("fields" in item or "id" in item for item in node):
                candidates.append(node)
        elif isinstance(node, str):
            try:
                decoded = json.loads(node)
            except json.JSONDecodeError:
                continue
            extracted = _extract_records(decoded)
            if extracted:
                candidates.append(extracted)
    return max(candidates, key=len) if candidates else []


def _extract_next_token(payload: Any) -> str | None:
    keys = {"nextPageToken", "next_page_token", "offset", "nextOffset"}
    for node in _walk_json(payload):
        if isinstance(node, dict):
            for key in keys:
                value = node.get(key)
                if isinstance(value, str) and value:
                    return value
    return None


def _record_fields(record: dict[str, Any]) -> dict[str, Any]:
    fields = record.get("fields")
    return fields if isinstance(fields, dict) else {}


def _normalize_value(value: Any) -> Any:
    if isinstance(value, dict) and "name" in value:
        return value.get("name")
    if isinstance(value, list):
        return [_normalize_value(item) for item in value]
    if isinstance(value, float):
        return round(value, 9)
    return value


def _chunks(values: list[Any], size: int) -> Iterable[list[Any]]:
    for index in range(0, len(values), size):
        yield values[index:index + size]


def list_all_records(cli: AirtableCLI, mapping: dict[str, Any]) -> list[dict[str, Any]]:
    field_ids = [mapping["key"]["airtable_field_id"], *[field["airtable_field_id"] for field in mapping["fields"]]]
    records: list[dict[str, Any]] = []
    token: str | None = None
    seen_tokens: set[str] = set()
    for _ in range(1000):
        payload: dict[str, Any] = {
            "baseId": mapping["base_id"],
            "tableId": mapping["table_id"],
            "fieldIds": list(dict.fromkeys(field_ids)),
            "pageSize": int(mapping.get("page_size", 100)),
        }
        if token:
            payload["pageToken"] = token
        response = cli.call("list_records_for_table", payload)
        records.extend(_extract_records(response))
        token = _extract_next_token(response)
        if not token or token in seen_tokens:
            break
        seen_tokens.add(token)
    return records


def build_sync_preview(
    input_path: str | Path,
    mapping_path: str | Path,
    cli: AirtableCLI,
    output_path: str | Path,
) -> dict[str, Any]:
    mapping = load_airtable_mapping(mapping_path)
    headers, rows, _ = read_sheet(input_path, mapping["source_sheet"])
    index = {name: pos for pos, name in enumerate(headers)}
    required_columns = [mapping["key"]["excel_column"], *[field["excel_column"] for field in mapping["fields"]]]
    missing = [name for name in required_columns if name not in index]
    if missing:
        raise ValueError(f"Brak kolumn wymaganych przez mapowanie Airtable: {missing}")

    key_excel = mapping["key"]["excel_column"]
    key_field = mapping["key"]["airtable_field_id"]
    source_by_key: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row_number, row in enumerate(rows, start=2):
        key_value = row[index[key_excel]]
        key = str(key_value).strip() if key_value is not None else ""
        fields = {
            field["airtable_field_id"]: row[index[field["excel_column"]]]
            for field in mapping["fields"]
            if field.get("mode", "write") == "write"
        }
        source_by_key[key].append({"row": row_number, "key": key_value, "fields": fields})

    airtable_records = list_all_records(cli, mapping)
    remote_by_key: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in airtable_records:
        fields = _record_fields(record)
        key_value = fields.get(key_field)
        key = str(_normalize_value(key_value)).strip() if key_value is not None else ""
        remote_by_key[key].append(record)

    creates: list[dict[str, Any]] = []
    updates: list[dict[str, Any]] = []
    unchanged: list[dict[str, Any]] = []
    conflicts: list[dict[str, Any]] = []
    blocked: list[dict[str, Any]] = []

    for key, source_items in source_by_key.items():
        if not key:
            blocked.extend({"reason": "missing_key", **item} for item in source_items)
            continue
        if len(source_items) > 1:
            conflicts.append({"reason": "duplicate_key_in_workbook", "key": key, "rows": [item["row"] for item in source_items]})
            continue
        remote_items = remote_by_key.get(key, [])
        if len(remote_items) > 1:
            conflicts.append({"reason": "duplicate_key_in_airtable", "key": key, "record_ids": [item.get("id") for item in remote_items]})
            continue
        source_item = source_items[0]
        if not remote_items:
            creates.append({"key": key, "row": source_item["row"], "fields": {key_field: source_item["key"], **source_item["fields"]}})
            continue
        record = remote_items[0]
        remote_fields = _record_fields(record)
        changed = {
            field_id: value
            for field_id, value in source_item["fields"].items()
            if _normalize_value(remote_fields.get(field_id)) != _normalize_value(value)
        }
        if changed:
            updates.append({"key": key, "row": source_item["row"], "record_id": record.get("id"), "fields": changed})
        else:
            unchanged.append({"key": key, "row": source_item["row"], "record_id": record.get("id")})

    plan = {
        "plan_version": "0.2.0",
        "base_id": mapping["base_id"],
        "table_id": mapping["table_id"],
        "mapping_path": str(mapping_path),
        "input_path": str(input_path),
        "counts": {
            "create": len(creates),
            "update": len(updates),
            "unchanged": len(unchanged),
            "conflict": len(conflicts),
            "blocked": len(blocked),
        },
        "creates": creates,
        "updates": updates,
        "unchanged": unchanged,
        "conflicts": conflicts,
        "blocked": blocked,
    }
    plan["plan_sha256"] = canonical_json_hash(plan)
    write_json(output_path, plan)
    return plan


def create_approval_template(plan: dict[str, Any], output_path: str | Path) -> dict[str, Any]:
    approval = {
        "approved": False,
        "plan_sha256": plan["plan_sha256"],
        "allow_create": True,
        "allow_update": True,
        "max_create": plan["counts"]["create"],
        "max_update": plan["counts"]["update"],
        "approved_by": "",
        "note": "Ustaw approved=true dopiero po sprawdzeniu planu.",
    }
    write_json(output_path, approval)
    return approval


def apply_sync_plan(
    plan_path: str | Path,
    approval_path: str | Path,
    cli: AirtableCLI,
    output_report: str | Path,
) -> dict[str, Any]:
    plan = json.loads(Path(plan_path).read_text(encoding="utf-8"))
    approval = json.loads(Path(approval_path).read_text(encoding="utf-8"))
    expected = plan.get("plan_sha256")
    comparable = dict(plan)
    comparable.pop("plan_sha256", None)
    actual = canonical_json_hash(comparable)
    if expected != actual:
        raise ValueError("Plan został zmieniony po wygenerowaniu skrótu.")
    if approval.get("plan_sha256") != expected:
        raise ValueError("Zatwierdzenie dotyczy innego planu.")
    if approval.get("approved") is not True:
        raise PermissionError("Zapis wymaga approved=true.")
    if plan["counts"]["conflict"] or plan["counts"]["blocked"]:
        raise PermissionError("Plan zawiera konflikty lub rekordy zablokowane.")
    if plan["counts"]["create"] > int(approval.get("max_create", -1)):
        raise PermissionError("Liczba rekordów do utworzenia przekracza zatwierdzony limit.")
    if plan["counts"]["update"] > int(approval.get("max_update", -1)):
        raise PermissionError("Liczba aktualizacji przekracza zatwierdzony limit.")

    batch_size = 10
    create_responses: list[Any] = []
    update_responses: list[Any] = []
    if approval.get("allow_create", False):
        for batch in _chunks(plan["creates"], batch_size):
            create_responses.append(cli.call("create_records_for_table", {
                "baseId": plan["base_id"],
                "tableId": plan["table_id"],
                "records": [{"fields": item["fields"]} for item in batch],
            }))
    elif plan["creates"]:
        raise PermissionError("Plan zawiera tworzenie rekordów, ale allow_create=false.")

    if approval.get("allow_update", False):
        for batch in _chunks(plan["updates"], batch_size):
            update_responses.append(cli.call("update_records_for_table", {
                "baseId": plan["base_id"],
                "tableId": plan["table_id"],
                "records": [{"id": item["record_id"], "fields": item["fields"]} for item in batch],
            }))
    elif plan["updates"]:
        raise PermissionError("Plan zawiera aktualizacje, ale allow_update=false.")

    report = {
        "plan_sha256": expected,
        "approved_by": approval.get("approved_by"),
        "created": plan["counts"]["create"],
        "updated": plan["counts"]["update"],
        "create_batches": len(create_responses),
        "update_batches": len(update_responses),
        "responses": {"create": create_responses, "update": update_responses},
    }
    write_json(output_report, report)
    return report
