from cowrie_observer.anonymizer import anonymize_ip, anonymize_source_ip
from cowrie_observer.normalizer import normalize_event


def test_anonymize_ipv4_replaces_last_octet_with_zero() -> None:
    assert anonymize_ip("192.0.2.123") == "192.0.2.0"


def test_anonymize_ipv6_uses_network_prefix() -> None:
    assert anonymize_ip("2001:db8::1234") == "2001:db8::/64"


def test_anonymize_invalid_ip_returns_none() -> None:
    assert anonymize_ip("not-an-ip") is None


def test_anonymize_source_ip_returns_new_event_without_mutating_original() -> None:
    original = normalize_event(
        {
            "eventid": "cowrie.login.failed",
            "timestamp": "2026-01-01T00:00:00Z",
            "src_ip": "198.51.100.42",
        }
    )

    anonymized = anonymize_source_ip(original)

    assert original.source_ip == "198.51.100.42"
    assert anonymized.source_ip == "198.51.100.0"
    assert anonymized.event_id == original.event_id


def test_anonymize_event_without_source_ip() -> None:
    original = normalize_event({"eventid": "cowrie.command.input"})

    anonymized = anonymize_source_ip(original)

    assert anonymized.source_ip is None
