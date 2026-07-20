from pathlib import Path

from cowrie_observer.parser import iter_json_events, parse_json_lines

FIXTURES = Path(__file__).parent / "fixtures"


def test_iter_json_events_reads_valid_json_lines() -> None:
    events = list(iter_json_events(FIXTURES / "valid_events.jsonl"))

    assert len(events) == 2
    assert events[0]["eventid"] == "cowrie.login.failed"
    assert events[1]["input"] == "uname -a"


def test_parse_json_lines_skips_malformed_lines_and_counts_errors() -> None:
    result = parse_json_lines(FIXTURES / "malformed_events.jsonl")

    assert len(result.events) == 2
    assert result.error_count == 1
    assert result.errors[0].line_number == 2


def test_parse_json_lines_handles_empty_file() -> None:
    result = parse_json_lines(FIXTURES / "empty.jsonl")

    assert result.events == []
    assert result.errors == []
    assert result.error_count == 0


def test_iter_json_events_reads_incrementally(monkeypatch) -> None:
    read_calls = 0
    original_open = Path.open

    def counting_open(self: Path, *args, **kwargs):
        nonlocal read_calls
        handle = original_open(self, *args, **kwargs)
        original_read = handle.read

        def forbidden_read(*read_args, **read_kwargs):
            nonlocal read_calls
            read_calls += 1
            return original_read(*read_args, **read_kwargs)

        handle.read = forbidden_read
        return handle

    monkeypatch.setattr(Path, "open", counting_open)

    events = list(iter_json_events(FIXTURES / "valid_events.jsonl"))

    assert len(events) == 2
    assert read_calls == 0
