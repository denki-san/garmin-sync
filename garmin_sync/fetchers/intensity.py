"""Daily intensity minutes (moderate + vigorous + weekly goal)."""
from __future__ import annotations

import logging

log = logging.getLogger("garmin_sync.fetch.intensity")


def fetch_intensity(gc, day: str) -> dict | None:
    try:
        data = gc.get_intensity_minutes_data(day)
    except Exception as e:
        log.debug("intensity fetch failed: %s", e)
        return None
    if not data:
        return None
    out: dict = {}
    if data.get("moderateMinutes") is not None:
        out["moderate_min"] = data["moderateMinutes"]
    if data.get("vigorousMinutes") is not None:
        out["vigorous_min"] = data["vigorousMinutes"]
    if data.get("weekGoal") is not None:
        out["weekly_goal_min"] = data["weekGoal"]
    return out or None
