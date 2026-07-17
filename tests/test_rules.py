import json
import unittest
from pathlib import Path

from airtable_workbook_agent.rules import analyze_rows, apply_safe_changes


CONTRACT = json.loads((Path(__file__).parents[1] / "contracts" / "product_workbook_contract.json").read_text(encoding="utf-8"))
HEADERS = CONTRACT["required_columns"]


def row(**overrides):
    base = {
        "ID produktu": 1,
        "SKU": "ABC-1",
        "Nazwa produktu": "Produkt 1",
        "Kategoria główna": "Staw",
        "Podkategoria": "Preparaty",
        "Rozmiar / wariant": "1 kg",
        "Waga kg": 1.1,
        "Cena netto": 10.0,
        "Stan": 5,
        "Aktywny": True,
        "EAN": "5901234123457",
    }
    base.update(overrides)
    return [base[name] for name in HEADERS]


class RuleTests(unittest.TestCase):
    def test_valid_row_has_no_findings(self):
        result = analyze_rows(HEADERS, [row()], CONTRACT)
        self.assertEqual(result.findings, [])

    def test_duplicate_sku_is_blocker(self):
        result = analyze_rows(HEADERS, [row(), row(**{"ID produktu": 2})], CONTRACT)
        codes = [item.code for item in result.findings]
        self.assertIn("DUPLICATE_SKU", codes)
        self.assertTrue(result.blockers)

    def test_duplicate_name_requires_review_not_merge(self):
        result = analyze_rows(HEADERS, [row(), row(**{"ID produktu": 2, "SKU": "ABC-2", "EAN": "5901234123458"})], CONTRACT)
        findings = [item for item in result.findings if item.code == "DUPLICATE_NAZWA_PRODUKTU"]
        self.assertEqual(len(findings), 2)
        self.assertTrue(all(item.severity == "REVIEW" for item in findings))

    def test_invalid_ean_and_zero_price(self):
        result = analyze_rows(HEADERS, [row(**{"EAN": "123", "Cena netto": 0})], CONTRACT)
        codes = {item.code for item in result.findings}
        self.assertIn("INVALID_EAN_LENGTH", codes)
        self.assertIn("NON_POSITIVE_PRICE", codes)

    def test_suspect_variant_code_is_warning(self):
        result = analyze_rows(HEADERS, [row(**{"Rozmiar / wariant": "6-12 cm / 612 cm"})], CONTRACT)
        finding = next(item for item in result.findings if item.code == "SUSPECT_VARIANT_CODE")
        self.assertEqual(finding.severity, "WARNING")

    def test_whitespace_change_is_safe_only(self):
        dirty = row(**{"Nazwa produktu": "  Produkt   1  "})
        result = analyze_rows(HEADERS, [dirty], CONTRACT)
        self.assertEqual(len(result.safe_changes), 1)
        cleaned = apply_safe_changes(HEADERS, [dirty])
        self.assertEqual(cleaned[0][HEADERS.index("Nazwa produktu")], "Produkt 1")

    def test_missing_weight_allowed_for_live_fish(self):
        result = analyze_rows(HEADERS, [row(**{"Podkategoria": "Ryby żywe i ozdobne", "Waga kg": None})], CONTRACT)
        self.assertNotIn("MISSING_WEIGHT", {item.code for item in result.findings})


if __name__ == "__main__":
    unittest.main()
