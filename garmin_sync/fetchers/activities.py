"""Per-day activities list."""
from __future__ import annotations

import logging

log = logging.getLogger("garmin_sync.fetch.activities")


def fetch_activities(client, day: str) -> list[dict] | None:
    try:
        activities = client.connectapi(
            f"/activitylist-service/activities/search/activities?startDate={day}&endDate={day}"
        )
        if not activities:
            return None
        out: list[dict] = []
        for a in activities:
            entry: dict = {"name": a.get("activityName", "未知活动")}
            duration = a.get("duration")
            distance = a.get("distance")
            calories = a.get("calories")
            if duration:
                entry["duration_sec"] = int(duration)
            if distance:
                entry["distance_km"] = round(distance / 1000.0, 3)
            if calories:
                entry["calories"] = int(calories)
            out.append(entry)
        return out or None
    except Exception as e:
        log.debug("activities fetch failed: %s", e)
        return None
