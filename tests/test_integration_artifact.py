import tempfile
import unittest
from pathlib import Path

from openpyxl import Workbook

from airtable_workbook_agent.runtime import prepare_workbook
from airtable_workbook_agent.xlsx_backend import sha256_file


class LocalIntegrationTests(unittest.TestCase):
    def test_full_run_works_without_artifact_tool(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "input.xlsx"
            output = root / "output.xlsx"
            run_dir = root / "run"
            wb = Workbook()
            ws = wb.active
            ws.title = "EXPORT"
            ws.append([
                "ID produktu", "SKU", "Nazwa produktu", "Kategoria główna", "Podkategoria",
                "Rozmiar / wariant", "Waga kg", "Cena netto", "Stan", "Aktywny", "EAN"
            ])
            ws.append([1, "SKU-1", "Karma dla ryb | 1 kg", "Ryby i rośliny", "Karma dla ryb", "1 kg", None, 10.0, 5, True, None])
            wb.save(source)
            before = sha256_file(source)
            result = prepare_workbook(source, output, run_dir)
            self.assertTrue(result["verification"]["passed"])
            self.assertEqual(before, sha256_file(source))
            self.assertTrue(output.exists())


if __name__ == "__main__":
    unittest.main()
