"""Steps, HRV (incl. detailed fields), SpO2 — three independent fetchers."""
from __future__ import annotations

import logging

log = logging.getLogger("garmin_sync.fetch.body")


def fetch_steps(gc, day: str) -> dict | None:
    try:
        steps_list = gc.get_daily_steps(day, day)
    except Exception as e:
        log.debug("steps fetch failed: %s", e)
        return None
    if not steps_list:
        return None
    s = steps_list[0]
    out: dict = {}
    if s.get("totalSteps") is not None:
        out["total"] = s["totalSteps"]
    if s.get("totalDistance") is not None:
        out["distance_km"] = round(s["totalDistance"] / 1000.0, 3)
    if s.get("stepGoal") is not None:
        out["goal"] = s["stepGoal"]
    return out or None


def fetch_hrv(gc, day: str) -> dict | None:
    """HRV summary + detailed (baseline, 5min high, feedback phrase)."""
    try:
        data = gc.get_hrv_data(day)
    except Exception as e:
        log.debug("hrv fetch failed: %s", e)
        return None
    if not data:
        return None
    summary = data.get("hrvSummary") or {}
    if not summary:
        return None
    out: dict = {}
    if summary.get("weeklyAvg") is not None:
        out["weekly_avg_ms"] = summary["weeklyAvg"]
    if summary.get("lastNightAvg") is not None:
        out["last_night_ms"] = summary["lastNightAvg"]
    if summary.get("status"):
        out["status"] = summary["status"]
    if summary.get("lastNight5MinHigh") is not None:
        out["last_night_5_min_high_ms"] = summary["lastNight5MinHigh"]
    baseline = summary.get("baseline") or {}
    bl_out: dict = {}
    if baseline.get("balancedLow") is not None:
        bl_out["balanced_low"] = baseline["balancedLow"]
    if baseline.get("balancedUpper") is not None:
        bl_out["balanced_upper"] = baseline["balancedUpper"]
    if baseline.get("markerValue") is not None:
        bl_out["marker_value"] = baseline["markerValue"]
    if bl_out:
        out["baseline"] = bl_out
    if summary.get("feedbackPhrase"):
        out["feedback_phrase"] = summary["feedbackPhrase"]
    return out or None


def fetch_spo2(gc, day: str) -> dict | None:
    # Call the raw endpoint to keep ``averageSpO2HR`` (which
    # ``Garmin.get_spo2_data`` strips from its return).
    try:
        spo2 = gc.connectapi(f"/wellness-service/wellness/dailySpo2/{day}")
    except Exception as e:
        log.debug("spo2 fetch failed: %s", e)
        return None
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
