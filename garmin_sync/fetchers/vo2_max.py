"""VO2 Max via garminconnect password-login (garth scope 403).

Single-day query frequently returns empty; we widen to a 1-year window if needed.
"""
from __future__ import annotations

import datetime
import logging

log = logging.getLogger("garmin_sync.fetch.vo2_max")


def fetch_vo2_max(gc_client, day: str) -> dict | None:
    if gc_client is None:
        return None
    try:
        base = f"{gc_client.garmin_connect_metrics_url}/{day}/{day}"
        vo2 = gc_client.connectapi(base)
        if not vo2:
            d = datetime.datetime.strptime(day, "%Y-%m-%d")
            start = (d - datetime.timedelta(days=365)).strftime("%Y-%m-%d")
            vo2 = gc_client.connectapi(f"{gc_client.garmin_connect_metrics_url}/{start}/{day}")
        if not vo2 or not isinstance(vo2, list):
            return None
        out: dict = {}
        for item in vo2:
            gen = item.get("generic", {})
            v = gen.get("vo2MaxValue")
            vp = gen.get("vo2MaxPreciseValue")
            if v is not None:
                out["running"] = round(v, 1)
                if vp is not None:
                    out["running_precise"] = round(vp, 1)
            cycling = item.get("cycling")
            if cycling and cycling.get("vo2MaxValue") is not None:
                out["cycling"] = round(cycling["vo2MaxValue"], 1)
        return out or None
    except Exception as e:
        log.debug("vo2 max fetch failed: %s", e)
        return None
