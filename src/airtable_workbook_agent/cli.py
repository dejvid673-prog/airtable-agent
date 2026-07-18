from __future__ import annotations

import argparse
import json
from pathlib import Path

from .airtable_cli import AirtableCLI
from .airtable_sync import apply_sync_plan, build_sync_preview, create_approval_template
from .runtime import prepare_workbook, verify_workbook


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

    doctor = sub.add_parser("doctor", help="Sprawdza lokalny runtime i Airtable MCP CLI.")
    doctor.add_argument("--profile")
    doctor.add_argument("--require-write", action="store_true")

    preview = sub.add_parser("airtable-preview", help="Tworzy plan create/update bez zapisu.")
    preview.add_argument("--input", required=True, type=Path)
    preview.add_argument("--mapping", required=True, type=Path)
    preview.add_argument("--plan", required=True, type=Path)
    preview.add_argument("--approval-template", type=Path)
    preview.add_argument("--profile")

    apply = sub.add_parser("airtable-apply", help="Wykonuje zatwierdzony plan Airtable.")
    apply.add_argument("--plan", required=True, type=Path)
    apply.add_argument("--approval", required=True, type=Path)
    apply.add_argument("--report", required=True, type=Path)
    apply.add_argument("--profile")
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
        result = AirtableCLI(profile=args.profile).doctor(require_write=args.require_write)
        print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2, default=str))
        return 0 if result.passed else 2
    if args.command == "airtable-preview":
        cli = AirtableCLI(profile=args.profile)
        doctor = cli.doctor(require_write=False)
        if not doctor.passed:
            print(json.dumps(doctor.to_dict(), ensure_ascii=False, indent=2, default=str))
            return 2
        plan = build_sync_preview(args.input, args.mapping, cli, args.plan)
        if args.approval_template:
            create_approval_template(plan, args.approval_template)
        print(json.dumps(plan, ensure_ascii=False, indent=2, default=str))
        return 0 if not plan["counts"]["conflict"] and not plan["counts"]["blocked"] else 3
    if args.command == "airtable-apply":
        cli = AirtableCLI(profile=args.profile)
        doctor = cli.doctor(require_write=True)
        if not doctor.passed:
            print(json.dumps(doctor.to_dict(), ensure_ascii=False, indent=2, default=str))
            return 2
        report = apply_sync_plan(args.plan, args.approval, cli, args.report)
        print(json.dumps(report, ensure_ascii=False, indent=2, default=str))
        return 0
    return 1
