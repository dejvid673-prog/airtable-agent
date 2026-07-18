from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .airtable_cli import AirtableCLI
from .airtable_rest import AirtableRESTClient
from .airtable_sync import apply_sync_plan, build_sync_preview, create_approval_template
from .runtime import prepare_workbook, verify_workbook


def _airtable_client(backend: str, profile: str | None) -> Any:
    if backend == "rest":
        return AirtableRESTClient()
    return AirtableCLI(profile=profile)


def _add_backend_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--backend",
        choices=("rest", "mcp"),
        default="rest",
        help="Transport Airtable. REST jest domyślny; MCP pozostaje opcjonalny.",
    )
    parser.add_argument("--profile", help="Profil airtable-mcp używany tylko z --backend mcp.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="airtable-workbook-agent")
    sub = parser.add_subparsers(dest="command", required=True)

    prepare = sub.add_parser("prepare", aliases=["run"], help="Porządkuje XLSX i tworzy raporty.")
    prepare.add_argument("--input", required=True, type=Path)
    prepare.add_argument("--output", required=True, type=Path)
    prepare.add_argument("--run-dir", required=True, type=Path)
    prepare.add_argument("--contract", type=Path)

    verify = sub.add_parser("verify", help="Weryfikuje przygotowany skoroszyt.")
    verify.add_argument("--input", required=True, type=Path)
    verify.add_argument("--output", required=True, type=Path)
    verify.add_argument("--contract", type=Path)

    doctor = sub.add_parser("doctor", help="Sprawdza dostęp do Airtable bez zapisu.")
    _add_backend_arguments(doctor)
    doctor.add_argument("--require-write", action="store_true")

    preview = sub.add_parser("airtable-preview", help="Tworzy plan create/update bez zapisu.")
    preview.add_argument("--input", required=True, type=Path)
    preview.add_argument("--mapping", required=True, type=Path)
    preview.add_argument("--plan", required=True, type=Path)
    preview.add_argument("--approval-template", type=Path)
    _add_backend_arguments(preview)

    apply = sub.add_parser("airtable-apply", help="Wykonuje zatwierdzony plan Airtable.")
    apply.add_argument("--plan", required=True, type=Path)
    apply.add_argument("--approval", required=True, type=Path)
    apply.add_argument("--report", required=True, type=Path)
    _add_backend_arguments(apply)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command in {"prepare", "run"}:
        result = prepare_workbook(args.input, args.output, args.run_dir, args.contract)
        print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
        return 0
    if args.command == "verify":
        result = verify_workbook(args.input, args.output, args.contract)
        print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
        return 0 if result["passed"] else 2
    if args.command == "doctor":
        result = _airtable_client(args.backend, args.profile).doctor(require_write=args.require_write)
        print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2, default=str))
        return 0 if result.passed else 2
    if args.command == "airtable-preview":
        client = _airtable_client(args.backend, args.profile)
        doctor = client.doctor(require_write=False)
        if not doctor.passed:
            print(json.dumps(doctor.to_dict(), ensure_ascii=False, indent=2, default=str))
            return 2
        plan = build_sync_preview(args.input, args.mapping, client, args.plan)
        plan["backend"] = args.backend
        if args.approval_template:
            create_approval_template(plan, args.approval_template)
        print(json.dumps(plan, ensure_ascii=False, indent=2, default=str))
        return 0 if not plan["counts"]["conflict"] and not plan["counts"]["blocked"] else 3
    if args.command == "airtable-apply":
        client = _airtable_client(args.backend, args.profile)
        doctor = client.doctor(require_write=True)
        if not doctor.passed:
            print(json.dumps(doctor.to_dict(), ensure_ascii=False, indent=2, default=str))
            return 2
        report = apply_sync_plan(args.plan, args.approval, client, args.report)
        report["backend"] = args.backend
        print(json.dumps(report, ensure_ascii=False, indent=2, default=str))
        return 0
    return 1
