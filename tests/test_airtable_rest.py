import json
import os
import unittest
from unittest.mock import patch

from airtable_workbook_agent.airtable_rest import AirtableRESTClient, AirtableRESTError


FULL_PAT = "patExample123456.secretExample123456"


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

    def test_rejects_visible_token_id_without_secret(self):
        with self.assertRaisesRegex(AirtableRESTError, "niepełny Personal Access Token"):
            AirtableRESTClient(token="patgBJ16dtt2yuYMD")

    @patch("urllib.request.urlopen")
    def test_doctor_validates_whoami_scopes_and_bases(self, urlopen):
        urlopen.side_effect = [
            FakeResponse({
                "id": "usr123",
                "scopes": ["data.records:read", "data.records:write", "schema.bases:read"],
            }),
            FakeResponse({"bases": [{"id": "app123"}]}),
        ]
        result = AirtableRESTClient(token=FULL_PAT).doctor(require_write=True)
        self.assertTrue(result.passed)
        self.assertEqual(result.user_id, "usr123")
        self.assertEqual(result.bases_visible, 1)
        self.assertEqual(result.missing_scopes, ())
        self.assertFalse(result.write_scope_verified)
        first_request = urlopen.call_args_list[0].args[0]
        second_request = urlopen.call_args_list[1].args[0]
        self.assertEqual(first_request.get_header("Authorization"), f"Bearer {FULL_PAT}")
        self.assertTrue(first_request.full_url.endswith("/v0/meta/whoami"))
        self.assertTrue(second_request.full_url.endswith("/v0/meta/bases"))

    @patch("urllib.request.urlopen")
    def test_doctor_reports_missing_scopes_without_listing_bases(self, urlopen):
        urlopen.return_value = FakeResponse({
            "id": "usr123",
            "scopes": ["data.records:read"],
        })
        result = AirtableRESTClient(token=FULL_PAT).doctor(require_write=True)
        self.assertFalse(result.passed)
        self.assertTrue(result.authenticated)
        self.assertEqual(
            result.missing_scopes,
            ("data.records:write", "schema.bases:read"),
        )
        self.assertEqual(urlopen.call_count, 1)

    @patch("urllib.request.urlopen")
    def test_list_records_uses_field_ids_and_offset(self, urlopen):
        urlopen.return_value = FakeResponse({"records": [], "offset": "next"})
        client = AirtableRESTClient(token=FULL_PAT)
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
        client = AirtableRESTClient(token=FULL_PAT)
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
