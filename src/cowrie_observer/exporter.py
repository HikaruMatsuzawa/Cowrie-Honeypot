"""CSV exporters for public Cowrie analysis data."""

from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path

from cowrie_observer.anonymizer import anonymize_ip
from cowrie_observer.statistics import EventSummary


def export_public_summary_csv(summary: EventSummary, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    rows = [
        ("total_events", "all", summary.total_events),
        ("total_connections", "all", summary.total_connections),
        ("unique_source_ips", "all", summary.unique_source_ips),
        *(_counter_rows("events_by_id", summary.events_by_id)),
        *(_counter_rows("connections_by_day", summary.connections_by_day)),
        *(_counter_rows("connections_by_hour", summary.connections_by_hour)),
        *(_counter_rows("usernames", summary.usernames)),
        *(_counter_rows("source_ips", _anonymized_ip_counts(summary.source_ips))),
        *(_counter_rows("commands", summary.commands)),
        *(_session_command_rows(summary.commands_by_session)),
    ]

    with output_path.open("w", encoding="utf-8", newline="") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(["metric", "key", "value"])
        writer.writerows(rows)


def _counter_rows(metric: str, values: dict[str, int]) -> list[tuple[str, str, int]]:
    return [(metric, key, value) for key, value in sorted(values.items())]


def _anonymized_ip_counts(values: dict[str, int]) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for source_ip, count in values.items():
        anonymized = anonymize_ip(source_ip)
        if anonymized is not None:
            counts[anonymized] += count
    return dict(counts)


def _session_command_rows(values: dict[str, list[str]]) -> list[tuple[str, str, str]]:
    rows: list[tuple[str, str, str]] = []
    for session_id, commands in sorted(values.items()):
        rows.append(("commands_by_session", session_id, " | ".join(commands)))
    return rows
