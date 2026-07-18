from __future__ import annotations

import json
import os
import shutil
import subprocess
from dataclasses import dataclass
from typing import Any


class AirtableCLIError(RuntimeError):
    pass


@dataclass(frozen=True)
class AirtableDoctorResult:
    executable: str | None
    authenticated: bool
    tools: dict[str, str]
    missing_tools: list[str]
    raw_whoami: Any = None

    @property
    def passed(self) -> bool:
        return bool(self.executable and self.authenticated and not self.missing_tools)

    def to_dict(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "executable": self.executable,
            "authenticated": self.authenticated,
            "tools": self.tools,
            "missing_tools": self.missing_tools,
            "raw_whoami": self.raw_whoami,
        }


class AirtableCLI:
    REQUIRED_READ_TOOLS = {
        "search_bases",
        "list_tables_for_base",
        "get_table_schema",
        "list_records_for_table",
    }
    REQUIRED_WRITE_TOOLS = {
        "create_records_for_table",
        "update_records_for_table",
    }

    def __init__(self, executable: str = "airtable-mcp", profile: str | None = None, timeout: int = 120):
        self.executable = executable
        self.profile = profile
        self.timeout = timeout

    @property
    def resolved_executable(self) -> str | None:
        return shutil.which(self.executable)

    def _base_command(self) -> list[str]:
        executable = self.resolved_executable
        if not executable:
            raise AirtableCLIError(
                "Nie znaleziono airtable-mcp. Zainstaluj: npm install -g @airtable/mcp-cli"
            )
        return [executable]

    def _run(self, args: list[str], payload: dict[str, Any] | None = None) -> Any:
        command = [*self._base_command(), *args]
        if self.profile:
            command.extend(["--profile", self.profile])
        try:
            process = subprocess.run(
                command,
                input=json.dumps(payload, ensure_ascii=False) if payload is not None else None,
                text=True,
                capture_output=True,
                timeout=self.timeout,
                env=os.environ.copy(),
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise AirtableCLIError(f"Przekroczono czas wykonania: {' '.join(command)}") from exc
        if process.returncode != 0:
            message = process.stderr.strip() or process.stdout.strip() or f"Kod wyjścia {process.returncode}"
            raise AirtableCLIError(message)
        output = process.stdout.strip()
        if not output:
            return None
        try:
            return json.loads(output)
        except json.JSONDecodeError:
            return output

    def whoami(self) -> Any:
        return self._run(["whoami"])

    def tools(self, refresh: bool = False) -> list[dict[str, Any]]:
        args = ["tools", "--json"]
        if refresh:
            args.append("--refresh")
        result = self._run(args)
        if not isinstance(result, list):
            raise AirtableCLIError("Nieoczekiwany format `airtable-mcp tools --json`.")
        return result

    def call(self, tool_name: str, payload: dict[str, Any]) -> Any:
        cli_name = tool_name.replace("_", "-")
        return self._run([cli_name, "--input", "-", "-q"], payload)

    def doctor(self, require_write: bool = False) -> AirtableDoctorResult:
        executable = self.resolved_executable
        if not executable:
            required = sorted(self.REQUIRED_READ_TOOLS | (self.REQUIRED_WRITE_TOOLS if require_write else set()))
            return AirtableDoctorResult(None, False, {}, required)
        try:
            whoami = self.whoami()
            authenticated = True
        except AirtableCLIError as exc:
            whoami = str(exc)
            authenticated = False
        try:
            tools = self.tools(refresh=True)
        except AirtableCLIError:
            tools = []
        access_map = {str(item.get("name")): str(item.get("access", "unknown")) for item in tools if item.get("name")}
        normalized = {name.replace("-", "_"): access for name, access in access_map.items()}
        required = self.REQUIRED_READ_TOOLS | (self.REQUIRED_WRITE_TOOLS if require_write else set())
        missing = sorted(name for name in required if name not in normalized)
        return AirtableDoctorResult(executable, authenticated, normalized, missing, whoami)
