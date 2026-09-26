from __future__ import annotations

import argparse
from pathlib import Path
import sys

from .core import RunLedgerError, record, write_receipt


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="runledger",
        description="Create a local execution receipt for a command.",
    )
    parser.add_argument("--cwd", type=Path, default=Path.cwd())
    parser.add_argument("--receipt", type=Path, default=Path("runledger-receipt.json"))
    parser.add_argument("--env", action="append", default=[], metavar="NAME")
    parser.add_argument("--input", action="append", default=[], metavar="PATH")
    parser.add_argument("--output", action="append", default=[], metavar="PATH")
    parser.add_argument("command", nargs=argparse.REMAINDER)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    command = list(args.command)
    if command and command[0] == "--":
        command.pop(0)
    try:
        cwd = args.cwd.resolve()
        receipt, code = record(
            command, cwd=cwd, env_names=args.env,
            input_paths=args.input, output_paths=args.output,
        )
        target = args.receipt if args.receipt.is_absolute() else cwd / args.receipt
        write_receipt(target, receipt)
        return code
    except RunLedgerError as exc:
        print(f"runledger: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
