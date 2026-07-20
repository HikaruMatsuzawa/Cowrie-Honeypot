"""Cowrie JSON Lines log parser."""

from __future__ import annotations

import json
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any

JsonEvent = dict[str, Any]


@dataclass(frozen=True)
class ParseError:
    line_number: int
    message: str
    raw_line: str


@dataclass(frozen=True)
class ParseResult:
    events: list[JsonEvent]
    errors: list[ParseError]

    @property
    def error_count(self) -> int:
        return len(self.errors)


def iter_json_events(path: Path) -> Iterator[JsonEvent]:
    """Yield valid JSON object lines from a Cowrie JSON Lines log."""
    with path.open("r", encoding="utf-8") as log_file:
        for raw_line in log_file:
            line = raw_line.strip()
            if not line:
                continue

            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue

            if isinstance(event, dict):
                yield event


def parse_json_lines(path: Path) -> ParseResult:
    events: list[JsonEvent] = []
    errors: list[ParseError] = []

    with path.open("r", encoding="utf-8") as log_file:
        for line_number, raw_line in enumerate(log_file, start=1):
            line = raw_line.strip()
            if not line:
                continue

            try:
                event = json.loads(line)
            except json.JSONDecodeError as exc:
                errors.append(
                    ParseError(
                        line_number=line_number,
                        message=exc.msg,
                        raw_line=raw_line.rstrip("\n"),
                    )
                )
                continue

            if isinstance(event, dict):
                events.append(event)
            else:
                errors.append(
                    ParseError(
                        line_number=line_number,
                        message="JSON line must contain an object",
                        raw_line=raw_line.rstrip("\n"),
                    )
                )

    return ParseResult(events=events, errors=errors)
