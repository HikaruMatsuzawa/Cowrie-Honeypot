"""Command line interface for Cowrie observer."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from cowrie_observer.exporter import export_public_summary_csv
from cowrie_observer.normalizer import normalize_events
from cowrie_observer.parser import parse_json_lines
from cowrie_observer.statistics import summarize_events


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command == "analyze":
        return _run_analyze(input_path=args.input, output_path=args.output)

    parser.error("unknown command")
    return 2


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="cowrie-observer")
    subparsers = parser.add_subparsers(dest="command", required=True)

    analyze = subparsers.add_parser("analyze")
    analyze.add_argument("--input", required=True, type=Path)
    analyze.add_argument("--output", required=True, type=Path)

    return parser


def _run_analyze(input_path: Path, output_path: Path) -> int:
    if not input_path.exists():
        print(
            f"Input log file not found: {input_path}\n"
            "Confirm that Cowrie has generated a JSON log, for example: ls -l logs/cowrie",
            file=sys.stderr,
        )
        return 1

    parse_result = parse_json_lines(input_path)
    events = normalize_events(parse_result.events)
    summary = summarize_events(events)
    try:
        export_public_summary_csv(summary, output_path)
    except PermissionError as exc:
        print(
            f"Cannot write output file: {output_path}\n"
            f"{exc}\n"
            "Confirm that the output directory is writable by the current user.",
            file=sys.stderr,
        )
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
