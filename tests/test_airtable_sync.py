import json
import tempfile
import unittest
from pathlib import Path

from openpyxl import Workbook

from airtable_workbook_agent.airtable_sync import apply_sync_plan, build_sync_preview, create_approval_template


class FakeCLI:
    def __init__(self, records=None):
        self.records = records or []
        self.calls = []

    def call(self, tool_name, payload):
        self.calls.append((tool_name, payload))
        if tool_name == "list_records_for_table":
            return {"records": self.records}
        if tool_name in {"create_records_for_table", "update_records_for_table"}:
            return {"ok": True, "count": len(payload["records"])}
        raise AssertionError(tool_name)


class AirtableSyncTests(unittest.TestCase):
    def _create_workbook(self, path: Path):
        wb = Workbook()
        ws = wb.active
        ws.title = "EXPORT_GOTOWY"
        ws.append(["SKU", "Nazwa produktu", "Cena netto"])
        ws.append(["A", "Produkt A", 10.0])
        ws.append(["B", "Produkt B", 20.0])
        wb.save(path)

    def _create_mapping(self, path: Path):
        path.write_text(json.dumps({
            "base_id": "app1",
            "table_id": "tbl1",
            "source_sheet": "EXPORT_GOTOWY",
            "key": {"excel_column": "SKU", "airtable_field_id": "fldSku"},
            "fields": [
                {"excel_column": "Nazwa produktu", "airtable_field_id": "fldName", "mode": "write"},
                {"excel_column": "Cena netto", "airtable_field_id": "fldPrice", "mode": "write"}
            ]
        }), encoding="utf-8")

    def test_preview_and_approved_apply(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            workbook = root / "input.xlsx"
            mapping = root / "mapping.json"
            plan_path = root / "plan.json"
            approval_path = root / "approval.json"
            report_path = root / "report.json"
            self._create_workbook(workbook)
            self._create_mapping(mapping)
            cli = FakeCLI(records=[{"id": "recA", "fields": {"fldSku": "A", "fldName": "Produkt A", "fldPrice": 9.0}}])
            plan = build_sync_preview(workbook, mapping, cli, plan_path)
            self.assertEqual(plan["counts"], {"create": 1, "update": 1, "unchanged": 0, "conflict": 0, "blocked": 0})
            approval = create_approval_template(plan, approval_path)
            approval["approved"] = True
            approval["approved_by"] = "test"
            approval_path.write_text(json.dumps(approval), encoding="utf-8")
            report = apply_sync_plan(plan_path, approval_path, cli, report_path)
            self.assertEqual(report["created"], 1)
            self.assertEqual(report["updated"], 1)
            self.assertTrue(any(name == "create_records_for_table" for name, _ in cli.calls))
            self.assertTrue(any(name == "update_records_for_table" for name, _ in cli.calls))

    def test_apply_rejects_unapproved_plan(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            workbook = root / "input.xlsx"
            mapping = root / "mapping.json"
            plan_path = root / "plan.json"
            approval_path = root / "approval.json"
            self._create_workbook(workbook)
            self._create_mapping(mapping)
            cli = FakeCLI()
            plan = build_sync_preview(workbook, mapping, cli, plan_path)
            create_approval_template(plan, approval_path)
            with self.assertRaises(PermissionError):
                apply_sync_plan(plan_path, approval_path, cli, root / "report.json")


if __name__ == "__main__":
    unittest.main()
