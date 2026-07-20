from cowrie_observer.normalizer import normalize_event


def test_normalize_login_failed_event() -> None:
    event = normalize_event(
        {
            "eventid": "cowrie.login.failed",
            "timestamp": "2026-01-01T00:00:00Z",
            "src_ip": "192.0.2.10",
            "src_port": 51234,
            "dst_port": 2222,
            "session": "session-1",
            "username": "root",
            "password": "admin",
        }
    )

    assert event.event_id == "cowrie.login.failed"
    assert event.timestamp == "2026-01-01T00:00:00Z"
    assert event.source_ip == "192.0.2.10"
    assert event.source_port == 51234
    assert event.destination_port == 2222
    assert event.session_id == "session-1"
    assert event.username == "root"
    assert event.password == "admin"
    assert event.command is None


def test_normalize_command_input_event() -> None:
    event = normalize_event(
        {
            "eventid": "cowrie.command.input",
            "timestamp": "2026-01-01T00:00:02Z",
            "src_ip": "198.51.100.20",
            "session": "session-2",
            "input": "uname -a",
        }
    )

    assert event.command == "uname -a"
    assert event.session_id == "session-2"


def test_normalize_missing_and_unknown_fields_without_crashing() -> None:
    event = normalize_event({"eventid": "cowrie.unknown"})

    assert event.event_id == "cowrie.unknown"
    assert event.timestamp is None
    assert event.source_ip is None
    assert event.username is None


def test_normalize_non_string_values_safely() -> None:
    event = normalize_event(
        {
            "eventid": 123,
            "src_ip": None,
            "src_port": "2222",
            "dst_port": "not-a-port",
            "username": 456,
        }
    )

    assert event.event_id == "123"
    assert event.source_ip is None
    assert event.source_port == 2222
    assert event.destination_port is None
    assert event.username == "456"
