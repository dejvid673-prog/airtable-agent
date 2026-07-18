import tempfile
import unittest
from pathlib import Path

from airtable_workbook_agent.reporting import write_json


class ReportingTests(unittest.TestCase):
    def test_json_is_utf8_and_keeps_polish_text(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "raport.json"
            write_json(path, {"opis": "Do weryfikacji"})
            self.assertIn("Do weryfikacji", path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
