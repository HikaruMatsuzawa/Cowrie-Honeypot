import csv

from cowrie_observer.exporter import export_public_summary_csv
from cowrie_observer.normalizer import normalize_event
from cowrie_observer.statistics import summarize_events


def test_export_public_summary_csv_omits_passwords_and_anonymizes_ips(tmp_path) -> None:
    events = [
        normalize_event(
            {
                "eventid": "cowrie.session.connect",
                "timestamp": "2026-01-01T00:10:00Z",
                "src_ip": "192.0.2.10",
            }
        ),
        normalize_event(
            {
                "eventid": "cowrie.login.failed",
                "timestamp": "2026-01-01T00:11:00Z",
                "src_ip": "198.51.100.42",
                "username": "root",
                "password": "admin",
            }
        ),
    ]
    output_path = tmp_path / "summary.csv"

    export_public_summary_csv(summarize_events(events), output_path)

    rows = list(csv.DictReader(output_path.open("r", encoding="utf-8", newline="")))

    assert {"metric", "key", "value"} == set(rows[0])
    assert {"metric": "source_ips", "key": "192.0.2.0", "value": "1"} in rows
    assert {"metric": "source_ips", "key": "198.51.100.0", "value": "1"} in rows
    assert not any(row["metric"] == "passwords" for row in rows)
    assert "198.51.100.42" not in output_path.read_text(encoding="utf-8")
    assert "admin" not in output_path.read_text(encoding="utf-8")
