from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any


class AirtableRESTError(RuntimeError):
    """Błąd odpowiedzi Airtable Web API."""


@dataclass(frozen=True)
class AirtableRESTDoctorResult:
    authenticated: bool
    backend: str
    bases_visible: int
    write_scope_verified: bool
    error: str | None = None

    @property
    def passed(self) -> bool:
        return self.authenticated and not self.error

    def to_dict(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "backend": self.backend,
            "authenticated": self.authenticated,
            "bases_visible": self.bases_visible,
            "write_scope_verified": self.write_scope_verified,
            "note": (
                "Uprawnienie zapisu jest weryfikowane dopiero przez zatwierdzony create/update; "
                "doctor nie wykonuje zmian w Airtable."
            ),
            "error": self.error,
        }


class AirtableRESTClient:
    """Minimalny klient oficjalnego Airtable Web API.

    Zachowuje interfejs ``call(tool_name, payload)`` używany przez istniejący
    silnik preview/apply, dzięki czemu zabezpieczenia planu nie zależą od
    transportu MCP.
    """

    API_ROOT = "https://api.airtable.com/v0"

    def __init__(self, token: str | None = None, timeout: int = 120):
        self.token = token or os.environ.get("AIRTABLE_TOKEN")
        self.timeout = timeout
        if not self.token:
            raise AirtableRESTError(
                "Brak AIRTABLE_TOKEN. Uruchom scripts/setup_airtable_rest.ps1."
            )

    def _request(
        self,
        method: str,
        path: str,
        *,
        query: list[tuple[str, str]] | None = None,
        payload: dict[str, Any] | None = None,
    ) -> Any:
        url = f"{self.API_ROOT}{path}"
        if query:
            url = f"{url}?{urllib.parse.urlencode(query)}"
        body = None
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/json",
        }
        if payload is not None:
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            headers["Content-Type"] = "application/json"
        request = urllib.request.Request(url, data=body, headers=headers, method=method)
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                content = response.read()
        except urllib.error.HTTPError as exc:
            raw = exc.read().decode("utf-8", errors="replace")
            try:
                decoded = json.loads(raw)
                message = decoded.get("error", decoded)
            except json.JSONDecodeError:
                message = raw or exc.reason
            raise AirtableRESTError(f"Airtable HTTP {exc.code}: {message}") from exc
        except urllib.error.URLError as exc:
            raise AirtableRESTError(f"Nie można połączyć się z Airtable Web API: {exc.reason}") from exc
        if not content:
            return None
        try:
            return json.loads(content.decode("utf-8"))
        except json.JSONDecodeError as exc:
            raise AirtableRESTError("Airtable zwrócił niepoprawny JSON.") from exc

    def list_bases(self) -> dict[str, Any]:
        return self._request("GET", "/meta/bases")

    def get_base_schema(self, base_id: str) -> dict[str, Any]:
        return self._request("GET", f"/meta/bases/{urllib.parse.quote(base_id)}/tables")

    def doctor(self, require_write: bool = False) -> AirtableRESTDoctorResult:
        try:
            payload = self.list_bases()
            bases = payload.get("bases", []) if isinstance(payload, dict) else []
            return AirtableRESTDoctorResult(
                authenticated=True,
                backend="rest",
                bases_visible=len(bases) if isinstance(bases, list) else 0,
                write_scope_verified=False,
            )
        except AirtableRESTError as exc:
            return AirtableRESTDoctorResult(
                authenticated=False,
                backend="rest",
                bases_visible=0,
                write_scope_verified=False,
                error=str(exc),
            )

    def _records_path(self, base_id: str, table_id: str) -> str:
        return f"/{urllib.parse.quote(base_id)}/{urllib.parse.quote(table_id)}"

    def call(self, tool_name: str, payload: dict[str, Any]) -> Any:
        base_id = str(payload.get("baseId", ""))
        table_id = str(payload.get("tableId", ""))
        if tool_name == "list_records_for_table":
            query: list[tuple[str, str]] = [
                ("pageSize", str(min(int(payload.get("pageSize", 100)), 100))),
                ("returnFieldsByFieldId", "true"),
            ]
            for field_id in payload.get("fieldIds", []):
                query.append(("fields[]", str(field_id)))
            token = payload.get("pageToken")
            if token:
                query.append(("offset", str(token)))
            return self._request("GET", self._records_path(base_id, table_id), query=query)

        if tool_name == "create_records_for_table":
            return self._request(
                "POST",
                self._records_path(base_id, table_id),
                payload={
                    "records": payload.get("records", []),
                    "typecast": False,
                    "returnFieldsByFieldId": True,
                },
            )

        if tool_name == "update_records_for_table":
            return self._request(
                "PATCH",
                self._records_path(base_id, table_id),
                payload={
                    "records": payload.get("records", []),
                    "typecast": False,
                    "returnFieldsByFieldId": True,
                },
            )

        if tool_name == "list_tables_for_base" or tool_name == "get_table_schema":
            return self.get_base_schema(base_id)

        if tool_name == "search_bases":
            return self.list_bases()

        raise AirtableRESTError(f"Nieobsługiwane narzędzie REST: {tool_name}")
