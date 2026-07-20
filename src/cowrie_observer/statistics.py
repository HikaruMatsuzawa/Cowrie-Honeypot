"""Aggregate normalized Cowrie events."""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass

from cowrie_observer.normalizer import NormalizedEvent


@dataclass(frozen=True)
class EventSummary:
    total_events: int
    total_connections: int
    unique_source_ips: int
    events_by_id: dict[str, int]
    connections_by_day: dict[str, int]
    connections_by_hour: dict[str, int]
    usernames: dict[str, int]
    passwords: dict[str, int]
    source_ips: dict[str, int]
    commands: dict[str, int]
    commands_by_session: dict[str, list[str]]


def summarize_events(events: list[NormalizedEvent]) -> EventSummary:
    events_by_id: Counter[str] = Counter()
    connections_by_day: Counter[str] = Counter()
    connections_by_hour: Counter[str] = Counter()
    usernames: Counter[str] = Counter()
    passwords: Counter[str] = Counter()
    source_ips: Counter[str] = Counter()
    commands: Counter[str] = Counter()
    commands_by_session: defaultdict[str, list[str]] = defaultdict(list)

    for event in events:
        events_by_id[event.event_id] += 1

        if event.source_ip is not None:
            source_ips[event.source_ip] += 1

        if event.username is not None:
            usernames[event.username] += 1

        if event.password is not None:
            passwords[event.password] += 1

        if event.event_id == "cowrie.session.connect":
            if event.timestamp is not None:
                connections_by_day[_day_key(event.timestamp)] += 1
                connections_by_hour[_hour_key(event.timestamp)] += 1

        if event.command is not None:
            commands[event.command] += 1
            if event.session_id is not None:
                commands_by_session[event.session_id].append(event.command)

    return EventSummary(
        total_events=len(events),
        total_connections=events_by_id["cowrie.session.connect"],
        unique_source_ips=len(source_ips),
        events_by_id=dict(events_by_id),
        connections_by_day=dict(connections_by_day),
        connections_by_hour=dict(connections_by_hour),
        usernames=dict(usernames),
        passwords=dict(passwords),
        source_ips=dict(source_ips),
        commands=dict(commands),
        commands_by_session=dict(commands_by_session),
    )


def _day_key(timestamp: str) -> str:
    return timestamp[:10]


def _hour_key(timestamp: str) -> str:
    return timestamp[:13]
