"""Body Battery via /wellness-service/wellness/bodyBattery/reports/daily.

API uses ``charged``/``drained`` (NOT bodyBatteryChargeValue).
"""
from __future__ import annotations

import logging

log = logging.getLogger("garmin_sync.fetch.body_battery")


def fetch_body_battery(gc, day: str) -> dict | None:
    try:
        data = gc.connectapi(
            "/wellness-service/wellness/bodyBattery/reports/daily",
            params={"startDate": day, "endDate": day},
        )
    except Exception as e:
        log.debug("body battery fetch failed: %s", e)
        return None
    if not data or not isinstance(data, list):
        return None
    entry = data[-1]
    out: dict = {}
    if entry.get("charged") is not None:
        out["charged"] = entry["charged"]
    if entry.get("drained") is not None:
        out["drained"] = entry["drained"]
    values_array = entry.get("bodyBatteryValuesArray", [])
    if values_array:
        levels = [v[1] for v in values_array if v[1] is not None]
        if levels:
            out["max"] = max(levels)
            out["min"] = min(levels)
    return out or None
