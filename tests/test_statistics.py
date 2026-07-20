from cowrie_observer.normalizer import normalize_event
from cowrie_observer.statistics import summarize_events


def test_summarize_events_counts_core_metrics() -> None:
    events = [
        normalize_event(
            {
                "eventid": "cowrie.session.connect",
                "timestamp": "2026-01-01T00:10:00Z",
                "src_ip": "192.0.2.10",
                "session": "session-1",
            }
        ),
        normalize_event(
            {
                "eventid": "cowrie.login.failed",
                "timestamp": "2026-01-01T00:11:00Z",
                "src_ip": "192.0.2.10",
                "session": "session-1",
                "username": "root",
                "password": "admin",
            }
        ),
        normalize_event(
            {
                "eventid": "cowrie.command.input",
                "timestamp": "2026-01-01T01:00:00Z",
                "src_ip": "198.51.100.20",
                "session": "session-2",
                "input": "uname -a",
            }
        ),
    ]

    summary = summarize_events(events)

    assert summary.total_events == 3
    assert summary.total_connections == 1
    assert summary.unique_source_ips == 2
    assert summary.events_by_id["cowrie.login.failed"] == 1
    assert summary.connections_by_day["2026-01-01"] == 1
    assert summary.connections_by_hour["2026-01-01T00"] == 1
    assert summary.usernames["root"] == 1
    assert summary.passwords["admin"] == 1
    assert summary.source_ips["192.0.2.10"] == 2
    assert summary.commands["uname -a"] == 1
    assert summary.commands_by_session["session-2"] == ["uname -a"]


def test_summarize_events_handles_empty_data() -> None:
    summary = summarize_events([])

    assert summary.total_events == 0
    assert summary.total_connections == 0
    assert summary.unique_source_ips == 0
    assert summary.events_by_id == {}


def test_summarize_events_ignores_missing_values() -> None:
    summary = summarize_events([normalize_event({"eventid": "cowrie.login.failed"})])

    assert summary.total_events == 1
    assert summary.unique_source_ips == 0
    assert summary.usernames == {}
    assert summary.passwords == {}
