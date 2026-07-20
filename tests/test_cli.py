import csv
import json
from unittest.mock import patch

from cowrie_observer.cli import main


def test_cli_analyze_generates_public_csv(tmp_path) -> None:
    input_path = tmp_path / "cowrie.jsonl"
    output_path = tmp_path / "summary.csv"
    input_path.write_text(
        "\n".join(
            [
                json.dumps(
                    {
                        "eventid": "cowrie.session.connect",
                        "timestamp": "2026-01-01T00:00:00Z",
                        "src_ip": "192.0.2.10",
                    }
                ),
                json.dumps(
                    {
                        "eventid": "cowrie.login.failed",
                        "timestamp": "2026-01-01T00:00:01Z",
                        "src_ip": "198.51.100.42",
                        "username": "root",
                        "password": "admin",
                    }
                ),
                json.dumps(
                    {
                        "eventid": "cowrie.command.input",
                        "timestamp": "2026-01-01T00:00:02Z",
                        "src_ip": "198.51.100.42",
                        "session": "s1",
                        "input": "uname -a",
                    }
                ),
            ]
        ),
        encoding="utf-8",
    )

    exit_code = main(["analyze", "--input", str(input_path), "--output", str(output_path)])

    rows = list(csv.DictReader(output_path.open("r", encoding="utf-8", newline="")))
    assert exit_code == 0
    assert {"metric": "total_events", "key": "all", "value": "3"} in rows
    assert {"metric": "source_ips", "key": "198.51.100.0", "value": "2"} in rows
    assert "admin" not in output_path.read_text(encoding="utf-8")


def test_cli_analyze_missing_input_returns_error(tmp_path, capsys) -> None:
    input_path = tmp_path / "missing.json"
    output_path = tmp_path / "summary.csv"

    exit_code = main(["analyze", "--input", str(input_path), "--output", str(output_path)])

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "Input log file not found" in captured.err
    assert not output_path.exists()


def test_cli_analyze_output_permission_error_returns_message(tmp_path, capsys) -> None:
    input_path = tmp_path / "cowrie.jsonl"
    output_path = tmp_path / "summary.csv"
    input_path.write_text(
        json.dumps(
            {
                "eventid": "cowrie.session.connect",
                "timestamp": "2026-01-01T00:00:00Z",
                "src_ip": "192.0.2.10",
            }
        ),
        encoding="utf-8",
    )

    with patch(
        "cowrie_observer.cli.export_public_summary_csv",
        side_effect=PermissionError("denied"),
    ):
        exit_code = main(["analyze", "--input", str(input_path), "--output", str(output_path)])

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "Cannot write output file" in captured.err
    assert "output directory is writable" in captured.err
