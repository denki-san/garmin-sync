"""Steps, HRV (incl. detailed fields), SpO2 — three independent fetchers."""
from __future__ import annotations

import logging
from datetime import date as _date

log = logging.getLogger("garmin_sync.fetch.body")


def fetch_steps(client, day: str) -> dict | None:
    from garth.stats.steps import DailySteps

    try:
        steps_list = DailySteps.list(end=_date.fromisoformat(day), period=1, client=client)
        if not steps_list:
            return None
        s = steps_list[0]
        out: dict = {}
        if s.total_steps is not None:
            out["total"] = s.total_steps
        if s.total_distance is not None:
            out["distance_km"] = round(s.total_distance / 1000.0, 3)
        if s.step_goal is not None:
            out["goal"] = s.step_goal
        return out or None
    except Exception as e:
        log.debug("steps fetch failed: %s", e)
        return None


def fetch_hrv(client, day: str) -> dict | None:
    """HRV summary + detailed (baseline, 5min high, feedback phrase)."""
    from garth.stats.hrv import DailyHRV

    try:
        hrv_list = DailyHRV.list(end=_date.fromisoformat(day), period=1, client=client)
        if not hrv_list:
            return None
        h = hrv_list[0]
        out: dict = {}
        if h.weekly_avg is not None:
            out["weekly_avg_ms"] = h.weekly_avg
        if h.last_night_avg is not None:
            out["last_night_ms"] = h.last_night_avg
        if h.status:
            out["status"] = h.status
        if h.last_night_5_min_high is not None:
            out["last_night_5_min_high_ms"] = h.last_night_5_min_high
        if h.baseline:
            b = h.baseline
            baseline: dict = {}
            if b.balanced_low is not None:
                baseline["balanced_low"] = b.balanced_low
            if b.balanced_upper is not None:
                baseline["balanced_upper"] = b.balanced_upper
            if b.marker_value is not None:
                baseline["marker_value"] = b.marker_value
            if baseline:
                out["baseline"] = baseline
        if h.feedback_phrase:
            out["feedback_phrase"] = h.feedback_phrase
        return out or None
    except Exception as e:
        log.debug("hrv fetch failed: %s", e)
        return None


def fetch_spo2(client, day: str) -> dict | None:
    try:
        spo2 = client.connectapi(f"/wellness-service/wellness/dailySpo2/{day}")
        if not spo2:
            return None
        out: dict = {}
        if spo2.get("averageSpO2"):
            out["avg_pct"] = spo2["averageSpO2"]
        if spo2.get("lowestSpO2"):
            out["min_pct"] = spo2["lowestSpO2"]
        if spo2.get("averageSpO2HR"):
            out["avg_hr_bpm"] = spo2["averageSpO2HR"]
        return out or None
    except Exception as e:
        log.debug("spo2 fetch failed: %s", e)
        return None
