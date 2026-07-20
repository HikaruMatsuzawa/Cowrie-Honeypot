"""Normalize Cowrie events into a stable internal shape."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from fractions import Fraction
from numbers import Integral
from typing import Any


@dataclass(frozen=True)
class NormalizedEvent:
    event_id: str
    timestamp: str | None = None
    source_ip: str | None = None
    source_port: int | None = None
    destination_port: int | None = None
    session_id: str | None = None
    username: str | None = None
    password: str | None = None
    command: str | None = None


def normalize_event(event: dict[str, Any]) -> NormalizedEvent:
    return NormalizedEvent(
        event_id=_optional_string(event.get("eventid")) or "unknown",
        timestamp=_optional_string(event.get("timestamp")),
        source_ip=_optional_string(event.get("src_ip")),
        source_port=_optional_int(event.get("src_port")),
        destination_port=_optional_int(event.get("dst_port")),
        session_id=_optional_string(event.get("session")),
        username=_optional_string(event.get("username")),
        password=_optional_string(event.get("password")),
        command=_optional_string(event.get("input")),
    )


def normalize_events(events: list[dict[str, Any]]) -> list[NormalizedEvent]:
    return [normalize_event(event) for event in events]


def _optional_string(value: object) -> str | None:
    if value is None:
        return None
    return str(value)


def _optional_int(value: object) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, Integral):
        return int(value)
    if isinstance(value, str):
        try:
            return int(value)
        except ValueError:
            return None
    if isinstance(value, bytes | bytearray):
        try:
            return int(value)
        except ValueError:
            return None
    if isinstance(value, float | Decimal | Fraction):
        return None
    return None
