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
    scopes: tuple[str, ...] = ()
    missing_scopes: tuple[str, ...] = ()
    user_id: str | None = None
    base_discovery_error: str | None = None
    error: str | None = None

    @property
    def passed(self) -> bool:
        return self.authenticated and not self.missing_scopes and not self.error

    def to_dict(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "backend": self.backend,
            "authenticated": self.authenticated,
            "user_id": self.user_id,
            "scopes": list(self.scopes),
            "missing_scopes": list(self.missing_scopes),
            "bases_visible": self.bases_visible,
            "base_discovery_error": self.base_discovery_error,
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
        self.token = (token or os.environ.get("AIRTABLE_TOKEN") or "").strip()
        self.timeout = timeout
        if not self.token:
            raise AirtableRESTError(
                "Brak AIRTABLE_TOKEN. Uruchom scripts/setup_airtable_rest.ps1."
            )
        if not self._looks_like_full_pat(self.token):
            raise AirtableRESTError(
                "Wklejono niepełny Personal Access Token. Pełny PAT zaczyna się od 'pat', "
                "zawiera kropkę i długi tajny ciąg po kropce. Token ID widoczny na liście "
                "tokenów nie wystarcza. W Airtable wybierz Regenerate token i skopiuj całość."
            )

    @staticmethod
    def _looks_like_full_pat(token: str) -> bool:
        if not token.startswith("pat") or "." not in token:
            return False
        token_id, secret = token.split(".", 1)
        return len(token_id) > 6 and len(secret) > 8

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
            "User-Agent": "airtable-product-workbook-agent/0.2.0",
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
                api_error = decoded.get("error", decoded)
                if isinstance(api_error, dict):
                    error_type = api_error.get("type")
                    error_message = api_error.get("message")
                    message = ": ".join(
                        str(item) for item in (error_type, error_message) if item
                    ) or str(api_error)
                else:
                    message = str(api_error)
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

    def whoami(self) -> dict[str, Any]:
        return self._request("GET", "/meta/whoami")

    def list_bases(self) -> dict[str, Any]:
        return self._request("GET", "/meta/bases")

    def get_base_schema(self, base_id: str) -> dict[str, Any]:
        return self._request("GET", f"/meta/bases/{urllib.parse.quote(base_id)}/tables")

    def doctor(self, require_write: bool = False) -> AirtableRESTDoctorResult:
        try:
            identity = self.whoami()
        except AirtableRESTError as exc:
            return AirtableRESTDoctorResult(
                authenticated=False,
                backend="rest",
                bases_visible=0,
                write_scope_verified=False,
                error=str(exc),
            )

        scopes = tuple(sorted(str(item) for item in identity.get("scopes", [])))
        required_scopes = {"data.records:read", "schema.bases:read"}
        if require_write:
            required_scopes.add("data.records:write")
        missing_scopes = tuple(sorted(required_scopes.difference(scopes)))

        bases_visible = 0
        base_discovery_error: str | None = None
        if not missing_scopes:
            try:
                payload = self.list_bases()
                bases = payload.get("bases", []) if isinstance(payload, dict) else []
                bases_visible = len(bases) if isinstance(bases, list) else 0
            except AirtableRESTError as exc:
                base_discovery_error = str(exc)

        return AirtableRESTDoctorResult(
            authenticated=True,
            backend="rest",
            bases_visible=bases_visible,
            write_scope_verified=False,
            scopes=scopes,
            missing_scopes=missing_scopes,
            user_id=str(identity.get("id")) if identity.get("id") else None,
            base_discovery_error=base_discovery_error,
            error=(
                "Token nie ma wymaganych zakresów: " + ", ".join(missing_scopes)
                if missing_scopes
                else None
            ),
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
                },
            )

        if tool_name == "update_records_for_table":
            return self._request(
                "PATCH",
                self._records_path(base_id, table_id),
                payload={
                    "records": payload.get("records", []),
                    "typecast": False,
                },
            )

        if tool_name == "list_tables_for_base" or tool_name == "get_table_schema":
            return self.get_base_schema(base_id)

        if tool_name == "search_bases":
            return self.list_bases()

        raise AirtableRESTError(f"Nieobsługiwane narzędzie REST: {tool_name}")
