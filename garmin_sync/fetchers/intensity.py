"""Daily intensity minutes (moderate + vigorous + weekly goal)."""
from __future__ import annotations

import logging
from datetime import date as _date

log = logging.getLogger("garmin_sync.fetch.intensity")


def fetch_intensity(client, day: str) -> dict | None:
    from garth.stats.intensity_minutes import DailyIntensityMinutes

    try:
        im_list = DailyIntensityMinutes.list(end=_date.fromisoformat(day), period=1, client=client)
        if not im_list:
            return None
        im = im_list[0]
        out: dict = {}
        if im.moderate_value is not None:
            out["moderate_min"] = im.moderate_value
        if im.vigorous_value is not None:
            out["vigorous_min"] = im.vigorous_value
        if im.weekly_goal is not None:
            out["weekly_goal_min"] = im.weekly_goal
        return out or None
    except Exception as e:
        log.debug("intensity fetch failed: %s", e)
        return None
