"""Tests for export.csv — uses fake JSON files, no network."""
from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

from garmin_sync.export.csv import COLUMNS, _flatten, export_csv


def _write_day(dir: Path, day: str, payload: dict) -> None:
    dir.mkdir(parents=True, exist_ok=True)
    payload = {"date": day, **payload}
    (dir / f"{day}.json").write_text(json.dumps(payload), encoding="utf-8")


def test_flatten_full_row():
    sample = {
        "date": "2026-05-28",
        "sleep": {
            "score": 88,
            "stages": {"total_min": 450, "deep_min": 114, "rem_min": 64,
                       "avg_respiration": 12.0, "avg_sleep_stress": 10.0},
        },
        "steps": {"total": 8833, "distance_km": 7.269, "goal": 7540},
        "hrv": {"weekly_avg_ms": 47, "last_night_ms": 46, "status": "BALANCED",
                "baseline": {"balanced_low": 39, "balanced_upper": 51}},
        "body_battery": {"charged": 86, "drained": 92, "max": 99, "min": 7},
        "stress": {"overall": 43, "level": "中", "rest_min": 494},
        "resting_heart_rate": {"value": 56.0},
        "vo2_max": {"running": 43.0},
        "activities": [{"name": "Run"}, {"name": "Walk"}],
    }
    row = _flatten(sample)
    assert row["date"] == "2026-05-28"
    assert row["sleep_score"] == 88
    assert row["sleep_total_min"] == 450
    assert row["sleep_rem_min"] == 64
    assert row["sleep_light_min"] == ""  # missing
    assert row["steps_total"] == 8833
    assert row["hrv_status"] == "BALANCED"
    assert row["hrv_baseline_low"] == 39
    assert row["stress_level"] == "中"
    assert row["resting_heart_rate"] == 56.0
    assert row["vo2_max_running"] == 43.0
    assert row["vo2_max_cycling"] == ""
    assert row["activities_count"] == 2


def test_flatten_empty_dict_all_blank():
    row = _flatten({"date": "2026-01-01"})
    assert row["date"] == "2026-01-01"
    blanks = [v for k, v in row.items() if k != "date" and k != "activities_count"]
    assert all(v == "" for v in blanks)
    # activities_count is always an int (default 0 when no list)
    assert row["activities_count"] == 0


def test_export_csv_writes_full_range_with_gaps(tmp_path):
    in_dir = tmp_path / "in"
    _write_day(in_dir, "2026-05-25", {"steps": {"total": 100}})
    _write_day(in_dir, "2026-05-27", {"steps": {"total": 300}})
    # 26 is missing — should still produce an (empty-data) row

    out = tmp_path / "out.csv"
    n = export_csv(in_dir, "2026-05-25", "2026-05-27", out)
    assert n == 3

    with open(out, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert [r["date"] for r in rows] == ["2026-05-25", "2026-05-26", "2026-05-27"]
    assert rows[0]["steps_total"] == "100"
    assert rows[1]["steps_total"] == ""  # gap day
    assert rows[2]["steps_total"] == "300"


def test_export_csv_header_matches_columns(tmp_path):
    _write_day(tmp_path, "2026-01-01", {})
    out = tmp_path / "h.csv"
    export_csv(tmp_path, "2026-01-01", "2026-01-01", out)
    with open(out, encoding="utf-8") as f:
        header = next(csv.reader(f))
    assert header == COLUMNS


def test_export_csv_rejects_bad_range(tmp_path):
    with pytest.raises(ValueError):
        export_csv(tmp_path, "2026-05-10", "2026-05-01", tmp_path / "x.csv")
