import importlib.util
import tempfile
import unittest
from pathlib import Path

ARTIFACT_AVAILABLE = importlib.util.find_spec("artifact_tool") is not None


@unittest.skipUnless(ARTIFACT_AVAILABLE, "artifact_tool nie jest dostępny w tym środowisku")
class ArtifactIntegrationTests(unittest.TestCase):
    def test_full_run_preserves_source_and_creates_audit_sheets(self):
        from artifact_tool import SpreadsheetFile, Workbook
        from airtable_workbook_agent.runtime import apply, sha256_file

        with tempfile.TemporaryDirectory() as temp:
            temp_path = Path(temp)
            source = temp_path / "input.xlsx"
            output = temp_path / "output.xlsx"
            run_dir = temp_path / "run"
            wb = Workbook.create()
            sheet = wb.worksheets.add("EXPORT")
            sheet.get_range("A1:K2").values = [[
                "ID produktu", "SKU", "Nazwa produktu", "Kategoria główna", "Podkategoria",
                "Rozmiar / wariant", "Waga kg", "Cena netto", "Stan", "Aktywny", "EAN"
            ], [1, "SKU-1", "Produkt", "Staw", "Preparaty", "1 kg", 1.1, 0, 5, True, "5901234123457"]]
            SpreadsheetFile.export_xlsx(wb).save(str(source))
            before = sha256_file(source)
            result = apply(source, output, run_dir)
            self.assertTrue(result["verification"]["passed"])
            self.assertEqual(before, sha256_file(source))
            self.assertTrue(output.exists())
            self.assertGreater(result["audit"]["metrics"]["findings"], 0)


if __name__ == "__main__":
    unittest.main()
