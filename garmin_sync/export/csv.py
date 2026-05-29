"""Flatten daily JSON files into a single CSV for spreadsheet / Grafana use."""
from __future__ import annotations

import csv
import logging
from datetime import date as _date, timedelta
from pathlib import Path

from ..storage import read_day_json

log = logging.getLogger("garmin_sync.export.csv")

# Fixed column order — keep this stable across releases so downstream sheets
# don't break. New metrics get appended to the end.
COLUMNS: list[str] = [
    "date",
    "sleep_score",
    "sleep_total_min",
    "sleep_deep_min",
    "sleep_light_min",
    "sleep_rem_min",
    "sleep_awake_min",
    "sleep_avg_spo2",
    "sleep_lowest_spo2",
    "sleep_avg_respiration",
    "sleep_avg_stress",
    "steps_total",
    "steps_distance_km",
    "steps_goal",
    "hrv_weekly_avg_ms",
    "hrv_last_night_ms",
    "hrv_status",
    "hrv_5min_high_ms",
    "hrv_baseline_low",
    "hrv_baseline_upper",
    "spo2_avg_pct",
    "spo2_min_pct",
    "spo2_avg_hr_bpm",
    "body_battery_charged",
    "body_battery_drained",
    "body_battery_max",
    "body_battery_min",
    "stress_overall",
    "stress_level",
    "stress_rest_min",
    "stress_low_min",
    "stress_medium_min",
    "stress_high_min",
    "respiration_low",
    "respiration_high",
    "respiration_avg",
    "intensity_moderate_min",
    "intensity_vigorous_min",
    "intensity_weekly_goal_min",
    "training_readiness_score",
    "training_readiness_status",
    "resting_heart_rate",
    "vo2_max_running",
    "vo2_max_cycling",
    "activities_count",
]


def _flatten(d: dict) -> dict[str, object]:
    """Project a daily JSON dict onto the flat ``COLUMNS`` schema."""
    row: dict[str, object] = {c: "" for c in COLUMNS}
    row["date"] = d.get("date", "")

    sleep = d.get("sleep") or {}
    row["sleep_score"] = sleep.get("score", "")
    stages = sleep.get("stages") or {}
    row["sleep_total_min"] = stages.get("total_min", "")
    row["sleep_deep_min"] = stages.get("deep_min", "")
    row["sleep_light_min"] = stages.get("light_min", "")
    row["sleep_rem_min"] = stages.get("rem_min", "")
    row["sleep_awake_min"] = stages.get("awake_min", "")
    row["sleep_avg_spo2"] = stages.get("avg_spo2", "")
    row["sleep_lowest_spo2"] = stages.get("lowest_spo2", "")
    row["sleep_avg_respiration"] = stages.get("avg_respiration", "")
    row["sleep_avg_stress"] = stages.get("avg_sleep_stress", "")

    steps = d.get("steps") or {}
    row["steps_total"] = steps.get("total", "")
    row["steps_distance_km"] = steps.get("distance_km", "")
    row["steps_goal"] = steps.get("goal", "")

    hrv = d.get("hrv") or {}
    row["hrv_weekly_avg_ms"] = hrv.get("weekly_avg_ms", "")
    row["hrv_last_night_ms"] = hrv.get("last_night_ms", "")
    row["hrv_status"] = hrv.get("status", "")
    row["hrv_5min_high_ms"] = hrv.get("last_night_5_min_high_ms", "")
    baseline = hrv.get("baseline") or {}
    row["hrv_baseline_low"] = baseline.get("balanced_low", "")
    row["hrv_baseline_upper"] = baseline.get("balanced_upper", "")

    spo2 = d.get("spo2") or {}
    row["spo2_avg_pct"] = spo2.get("avg_pct", "")
    row["spo2_min_pct"] = spo2.get("min_pct", "")
    row["spo2_avg_hr_bpm"] = spo2.get("avg_hr_bpm", "")

    bb = d.get("body_battery") or {}
    row["body_battery_charged"] = bb.get("charged", "")
    row["body_battery_drained"] = bb.get("drained", "")
    row["body_battery_max"] = bb.get("max", "")
    row["body_battery_min"] = bb.get("min", "")

    stress = d.get("stress") or {}
    row["stress_overall"] = stress.get("overall", "")
    row["stress_level"] = stress.get("level", "")
    row["stress_rest_min"] = stress.get("rest_min", "")
    row["stress_low_min"] = stress.get("low_min", "")
    row["stress_medium_min"] = stress.get("medium_min", "")
    row["stress_high_min"] = stress.get("high_min", "")

    resp = d.get("respiration") or {}
    row["respiration_low"] = resp.get("low", "")
    row["respiration_high"] = resp.get("high", "")
    row["respiration_avg"] = resp.get("avg", "")

    im = d.get("intensity_minutes") or {}
    row["intensity_moderate_min"] = im.get("moderate_min", "")
    row["intensity_vigorous_min"] = im.get("vigorous_min", "")
    row["intensity_weekly_goal_min"] = im.get("weekly_goal_min", "")

    tr = d.get("training_readiness") or {}
    row["training_readiness_score"] = tr.get("score", "")
    row["training_readiness_status"] = tr.get("status", "")

    rhr = d.get("resting_heart_rate") or {}
    row["resting_heart_rate"] = rhr.get("value", "")

    vo2 = d.get("vo2_max") or {}
    row["vo2_max_running"] = vo2.get("running", "")
    row["vo2_max_cycling"] = vo2.get("cycling", "")

    activities = d.get("activities") or []
    row["activities_count"] = len(activities)

    return row


def _iter_dates(start: str, end: str):
    s = _date.fromisoformat(start)
    e = _date.fromisoformat(end)
    if e < s:
        raise ValueError(f"end ({end}) must be on or after start ({start})")
    cur = s
    while cur <= e:
        yield cur.strftime("%Y-%m-%d")
        cur += timedelta(days=1)


def export_csv(input_dir: Path, start: str, end: str, out_path: Path) -> int:
    """Return number of rows written (one per date in [start, end])."""
    input_dir = Path(input_dir).expanduser()
    out_path = Path(out_path).expanduser()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    rows: list[dict] = []
    for day in _iter_dates(start, end):
        data = read_day_json(input_dir, day)
        if data is None:
            data = {"date": day}
            log.debug("no data for %s; emitting empty row", day)
        rows.append(_flatten(data))

    with open(out_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    return len(rows)
