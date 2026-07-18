import json
import unittest
from pathlib import Path

from airtable_workbook_agent.product_transform import PREPARED_HEADERS, transform_rows


CONTRACT = json.loads((Path(__file__).parents[1] / "contracts" / "product_workbook_contract.json").read_text(encoding="utf-8"))
HEADERS = CONTRACT["required_columns"]


def make_row(**overrides):
    base = {
        "ID produktu": 1,
        "SKU": "SKU-1",
        "Nazwa produktu": "Karma dla ryb | 4-35 cm | 1 kg",
        "Kategoria główna": "Ryby i rośliny",
        "Podkategoria": "Karma dla ryb",
        "Rozmiar / wariant": "4-35 cm / 1 kg",
        "Waga kg": None,
        "Cena netto": 10.0,
        "Stan": 5,
        "Aktywny": True,
        "EAN": "5901234123457",
    }
    base.update(overrides)
    return [base[name] for name in HEADERS]


class ProductTransformTests(unittest.TestCase):
    def test_maps_to_three_main_categories_and_extracts_measures(self):
        result = transform_rows(HEADERS, [make_row()], CONTRACT)
        row = dict(zip(PREPARED_HEADERS, result.rows[0]))
        self.assertEqual(row["Kategoria główna"], "Ryby")
        self.assertEqual(row["Podkategoria"], "Karma dla ryb")
        self.assertEqual(row["Nazwa produktu"], "Karma dla ryb")
        self.assertEqual(row["Rozmiar / długość"], "4-35 cm")
        self.assertEqual(row["Waga produktu kg"], 1.0)
        self.assertEqual(row["Waga wysyłkowa kg"], 1.1)
        self.assertEqual(row["Status agenta"], "OK")

    def test_line_strength_is_not_product_weight(self):
        source = make_row(
            **{
                "Nazwa produktu": "Żyłka Karpiowa | 0,4 mm | 500 m | 22 kg",
                "Kategoria główna": "Wędkarskie",
                "Podkategoria": "Żyłki i plecionki",
                "Rozmiar / wariant": "0,4 mm / 500 m / 22 kg",
            }
        )
        result = transform_rows(HEADERS, [source], CONTRACT)
        row = dict(zip(PREPARED_HEADERS, result.rows[0]))
        self.assertEqual(row["Kategoria główna"], "Wędkarstwo")
        self.assertEqual(row["Wytrzymałość kg"], 22.0)
        self.assertIsNone(row["Waga produktu kg"])
        self.assertIn("500 m", row["Rozmiar / długość"])

    def test_unmapped_subcategory_is_blocker(self):
        result = transform_rows(HEADERS, [make_row(**{"Podkategoria": "Nowa kategoria"})], CONTRACT)
        self.assertTrue(any(item.code == "UNMAPPED_SUBCATEGORY" and item.severity == "BLOCKER" for item in result.findings))

    def test_component_weight_is_separate(self):
        source = make_row(
            **{
                "Nazwa produktu": "Koszyk zanętowy | 150 g",
                "Kategoria główna": "Wędkarskie",
                "Podkategoria": "Akcesoria wędkarskie",
                "Rozmiar / wariant": "150 g",
            }
        )
        result = transform_rows(HEADERS, [source], CONTRACT)
        row = dict(zip(PREPARED_HEADERS, result.rows[0]))
        self.assertEqual(row["Ciężar elementu"], "150 g")
        self.assertIsNone(row["Waga produktu kg"])


if __name__ == "__main__":
    unittest.main()
