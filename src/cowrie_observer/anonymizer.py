"""Anonymize values before generating public analysis data."""

from __future__ import annotations

from dataclasses import replace
from ipaddress import ip_address, ip_network

from cowrie_observer.normalizer import NormalizedEvent


def anonymize_ip(value: str) -> str | None:
    try:
        address = ip_address(value)
    except ValueError:
        return None

    if address.version == 4:
        octets = value.split(".")
        return ".".join([*octets[:3], "0"])

    network = ip_network(f"{address}/64", strict=False)
    return f"{network.network_address}/64"


def anonymize_source_ip(event: NormalizedEvent) -> NormalizedEvent:
    if event.source_ip is None:
        return event
    return replace(event, source_ip=anonymize_ip(event.source_ip))
