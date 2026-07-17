from __future__ import annotations

import argparse
import json
from pathlib import Path

from .runtime import analyze, apply, verify


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="airtable-workbook-agent")
    sub = parser.add_subparsers(dest="command", required=True)

    analyze_parser = sub.add_parser("analyze", help="Analizuje XLSX bez modyfikacji.")
    analyze_parser.add_argument("--input", required=True, type=Path)
    analyze_parser.add_argument("--run-dir", required=True, type=Path)
    analyze_parser.add_argument("--contract", type=Path)

    run_parser = sub.add_parser("run", help="Wykonuje analyze → plan → apply → verify.")
    run_parser.add_argument("--input", required=True, type=Path)
    run_parser.add_argument("--output", required=True, type=Path)
    run_parser.add_argument("--run-dir", required=True, type=Path)
    run_parser.add_argument("--contract", type=Path)

    verify_parser = sub.add_parser("verify", help="Weryfikuje plik wynikowy.")
    verify_parser.add_argument("--input", required=True, type=Path)
    verify_parser.add_argument("--output", required=True, type=Path)
    verify_parser.add_argument("--contract", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "analyze":
        result = analyze(args.input, args.run_dir, args.contract)
        print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2, default=str))
        return 0
    if args.command == "run":
        result = apply(args.input, args.output, args.run_dir, args.contract)
        print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
        return 0
    if args.command == "verify":
        result = verify(args.input, args.output, args.contract)
        print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
        return 0 if result["passed"] else 2
    return 1
