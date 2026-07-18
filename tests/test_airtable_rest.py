import json
import os
import unittest
from unittest.mock import patch

from airtable_workbook_agent.airtable_rest import AirtableRESTClient, AirtableRESTError


class FakeResponse:
    def __init__(self, payload):
        self.payload = json.dumps(payload).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self):
        return self.payload


class AirtableRESTTests(unittest.TestCase):
    def test_requires_token(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(AirtableRESTError):
                AirtableRESTClient()

    @patch("urllib.request.urlopen")
    def test_doctor_validates_pat_without_write(self, urlopen):
        urlopen.return_value = FakeResponse({"bases": [{"id": "app123"}]})
        result = AirtableRESTClient(token="pat.test").doctor(require_write=True)
        self.assertTrue(result.passed)
        self.assertEqual(result.bases_visible, 1)
        self.assertFalse(result.write_scope_verified)
        request = urlopen.call_args.args[0]
        self.assertEqual(request.get_header("Authorization"), "Bearer pat.test")
        self.assertTrue(request.full_url.endswith("/v0/meta/bases"))

    @patch("urllib.request.urlopen")
    def test_list_records_uses_field_ids_and_offset(self, urlopen):
        urlopen.return_value = FakeResponse({"records": [], "offset": "next"})
        client = AirtableRESTClient(token="pat.test")
        payload = client.call("list_records_for_table", {
            "baseId": "app123",
            "tableId": "tbl123",
            "fieldIds": ["fldA", "fldB"],
            "pageSize": 100,
            "pageToken": "offset1",
        })
        self.assertEqual(payload["offset"], "next")
        url = urlopen.call_args.args[0].full_url
        self.assertIn("returnFieldsByFieldId=true", url)
        self.assertIn("fields%5B%5D=fldA", url)
        self.assertIn("offset=offset1", url)

    @patch("urllib.request.urlopen")
    def test_create_and_update_are_batched_json_requests(self, urlopen):
        urlopen.side_effect = [
            FakeResponse({"records": [{"id": "rec1"}]}),
            FakeResponse({"records": [{"id": "rec1"}]}),
        ]
        client = AirtableRESTClient(token="pat.test")
        client.call("create_records_for_table", {
            "baseId": "app123", "tableId": "tbl123",
            "records": [{"fields": {"fldA": "A"}}],
        })
        client.call("update_records_for_table", {
            "baseId": "app123", "tableId": "tbl123",
            "records": [{"id": "rec1", "fields": {"fldA": "B"}}],
        })
        first = urlopen.call_args_list[0].args[0]
        second = urlopen.call_args_list[1].args[0]
        self.assertEqual(first.method, "POST")
        self.assertEqual(second.method, "PATCH")
        self.assertEqual(json.loads(first.data), {
            "records": [{"fields": {"fldA": "A"}}],
            "typecast": False,
        })


if __name__ == "__main__":
    unittest.main()
