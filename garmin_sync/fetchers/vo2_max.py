"""VO2 Max via /metrics-service/metrics/maxmet/daily/{start}/{end}.

Single-day queries frequently return ``[]`` — the metric only updates after
a tagged run/ride. Widen to a 1-year window when the narrow query is empty.
"""
from __future__ import annotations

import datetime
import logging

log = logging.getLogger("garmin_sync.fetch.vo2_max")

BASE = "/metrics-service/metrics/maxmet/daily"


def fetch_vo2_max(gc, day: str) -> dict | None:
    try:
        vo2 = gc.connectapi(f"{BASE}/{day}/{day}")
        if not vo2:
            d = datetime.datetime.strptime(day, "%Y-%m-%d")
            start = (d - datetime.timedelta(days=365)).strftime("%Y-%m-%d")
            vo2 = gc.connectapi(f"{BASE}/{start}/{day}")
    except Exception as e:
        log.debug("vo2 max fetch failed: %s", e)
        return None
    if not vo2 or not isinstance(vo2, list):
        return None
    out: dict = {}
    for item in vo2:
        gen = item.get("generic") or {}
        v = gen.get("vo2MaxValue")
        vp = gen.get("vo2MaxPreciseValue")
        if v is not None:
            out["running"] = round(v, 1)
            if vp is not None:
                out["running_precise"] = round(vp, 1)
        cycling = item.get("cycling") or {}
        if cycling.get("vo2MaxValue") is not None:
            out["cycling"] = round(cycling["vo2MaxValue"], 1)
    return out or None
