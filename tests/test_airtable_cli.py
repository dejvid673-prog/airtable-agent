import json
import os
import stat
import sys
import tempfile
import unittest
from pathlib import Path

from airtable_workbook_agent.airtable_cli import AirtableCLI


FAKE_CLI = """import json, sys
if sys.argv[1] == 'whoami':
    print(json.dumps({'user':'ok'}))
elif sys.argv[1] == 'tools':
    print(json.dumps([
      {'name':'search_bases','access':'read-only'},
      {'name':'list_tables_for_base','access':'read-only'},
      {'name':'get_table_schema','access':'read-only'},
      {'name':'list_records_for_table','access':'read-only'},
      {'name':'create_records_for_table','access':'write'},
      {'name':'update_records_for_table','access':'write'}
    ]))
else:
    print(json.dumps({'ok':True}))
"""


class AirtableCLITests(unittest.TestCase):
    def test_doctor_discovers_required_tools(self):
        with tempfile.TemporaryDirectory() as temp:
            temp_path = Path(temp)
            helper = temp_path / "fake_airtable_mcp.py"
            helper.write_text(FAKE_CLI, encoding="utf-8")

            if os.name == "nt":
                wrapper = temp_path / "airtable-mcp.cmd"
                wrapper.write_text(
                    f'@echo off\r\n"{sys.executable}" "{helper}" %*\r\n',
                    encoding="utf-8",
                )
            else:
                wrapper = temp_path / "airtable-mcp"
                wrapper.write_text(
                    f"#!{sys.executable}\n{FAKE_CLI}",
                    encoding="utf-8",
                )
                wrapper.chmod(wrapper.stat().st_mode | stat.S_IEXEC)

            old_path = os.environ.get("PATH", "")
            os.environ["PATH"] = f"{temp}{os.pathsep}{old_path}"
            try:
                result = AirtableCLI().doctor(require_write=True)
            finally:
                os.environ["PATH"] = old_path

            self.assertTrue(result.passed)
            self.assertEqual(result.missing_tools, [])


if __name__ == "__main__":
    unittest.main()
