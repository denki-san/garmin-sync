"""Daily summary: floors, daily HR range, calories, activity-time breakdown.

One call to ``Garmin.get_stats(day)`` returns ~80 fields. We project a curated
subset into three sibling dicts: ``heart_rate``, ``calories``, ``floors``,
plus an ``activity_seconds`` rollup useful for sedentary-vs-active analysis.
"""
from __future__ import annotations

import logging

log = logging.getLogger("garmin_sync.fetch.daily_summary")


def fetch_daily_summary(gc, day: str) -> dict | None:
    """Return ``{heart_rate, calories, floors, activity_seconds}`` (any subset).

    The fetcher returns a single dict whose keys merge into the top-level
    JSON via :func:`collect_day`. Returns ``None`` only when the endpoint
    itself fails; otherwise an empty dict is suppressed by the caller.
    """
    try:
        s = gc.get_stats(day)
    except Exception as e:
        log.debug("daily summary fetch failed: %s", e)
        return None
    if not s:
        return None

    out: dict = {}

    hr: dict = {}
    if s.get("minHeartRate") is not None:
        hr["min"] = s["minHeartRate"]
    if s.get("maxHeartRate") is not None:
        hr["max"] = s["maxHeartRate"]
    if s.get("restingHeartRate") is not None:
        hr["resting"] = s["restingHeartRate"]
    if s.get("lastSevenDaysAvgRestingHeartRate") is not None:
        hr["last_7d_avg_resting"] = s["lastSevenDaysAvgRestingHeartRate"]
    if hr:
        out["heart_rate"] = hr

    cal: dict = {}
    if s.get("totalKilocalories") is not None:
        cal["total_kcal"] = int(s["totalKilocalories"])
    if s.get("activeKilocalories") is not None:
        cal["active_kcal"] = int(s["activeKilocalories"])
    if s.get("bmrKilocalories") is not None:
        cal["bmr_kcal"] = int(s["bmrKilocalories"])
    if s.get("consumedKilocalories") is not None:
        cal["consumed_kcal"] = int(s["consumedKilocalories"])
    if cal:
        out["calories"] = cal

    floors: dict = {}
    if s.get("floorsAscended") is not None:
        floors["ascended"] = s["floorsAscended"]
    if s.get("floorsDescended") is not None:
        floors["descended"] = s["floorsDescended"]
    if s.get("userFloorsAscendedGoal") is not None:
        floors["goal"] = s["userFloorsAscendedGoal"]
    if floors:
        out["floors"] = floors

    activity: dict = {}
    for src, dst in (
        ("highlyActiveSeconds", "highly_active_sec"),
        ("activeSeconds", "active_sec"),
        ("sedentarySeconds", "sedentary_sec"),
        ("sleepingSeconds", "sleeping_sec"),
    ):
        if s.get(src) is not None:
            activity[dst] = s[src]
    if activity:
        out["activity_seconds"] = activity

    return out or None
