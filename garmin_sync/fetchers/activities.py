"""Per-day activities list."""
from __future__ import annotations

import logging

log = logging.getLogger("garmin_sync.fetch.activities")


def fetch_activities(gc, day: str) -> list[dict] | None:
    try:
        activities = gc.connectapi(
            f"/activitylist-service/activities/search/activities?startDate={day}&endDate={day}"
        )
    except Exception as e:
        log.debug("activities fetch failed: %s", e)
        return None
    if not activities:
        return None
    out: list[dict] = []
    for a in activities:
        entry: dict = {"name": a.get("activityName", "未知活动")}
        if a.get("duration"):
            entry["duration_sec"] = int(a["duration"])
        if a.get("distance"):
            entry["distance_km"] = round(a["distance"] / 1000.0, 3)
        if a.get("calories"):
            entry["calories"] = int(a["calories"])
        out.append(entry)
    return out or None
