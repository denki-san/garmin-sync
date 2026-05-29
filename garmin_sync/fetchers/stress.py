"""Daily stress (overall 0-100 + bucket durations).

``garminconnect.get_stress_data`` returns the per-3-min chart but not the
aggregated bucket durations. We call the usersummary endpoint directly to
keep the JSON schema stable.
"""
from __future__ import annotations

import logging

log = logging.getLogger("garmin_sync.fetch.stress")


def _bucket(overall: int) -> str:
    if overall < 20:
        return "放松"
    if overall < 40:
        return "低"
    if overall < 60:
        return "中"
    if overall < 80:
        return "高"
    return "极高"


def fetch_stress(gc, day: str) -> dict | None:
    try:
        result = gc.connectapi(f"/usersummary-service/stats/stress/daily/{day}/{day}")
    except Exception as e:
        log.debug("stress fetch failed: %s", e)
        return None
    if not result or not isinstance(result, list):
        return None
    values = (result[0] or {}).get("values") or {}
    overall = values.get("overallStressLevel")
    if overall is None:
        return None
    out: dict = {"overall": overall, "level": _bucket(overall)}
    if values.get("restStressDuration") is not None:
        out["rest_min"] = round(values["restStressDuration"] / 60)
    if values.get("lowStressDuration") is not None:
        out["low_min"] = round(values["lowStressDuration"] / 60)
    if values.get("mediumStressDuration") is not None:
        out["medium_min"] = round(values["mediumStressDuration"] / 60)
    if values.get("highStressDuration") is not None:
        out["high_min"] = round(values["highStressDuration"] / 60)
    return out
