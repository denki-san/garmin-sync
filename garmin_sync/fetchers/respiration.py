"""Respiration via /wellness-service/wellness/daily/respiration/{date}."""
from __future__ import annotations

import logging

log = logging.getLogger("garmin_sync.fetch.respiration")


def fetch_respiration(gc, day: str) -> dict | None:
    try:
        data = gc.connectapi(f"/wellness-service/wellness/daily/respiration/{day}")
    except Exception as e:
        log.debug("respiration fetch failed: %s", e)
        return None
    if not data:
        return None
    out: dict = {}
    if data.get("averageRespirationValue") is not None:
        out["avg"] = round(data["averageRespirationValue"], 1)
    if data.get("lowestRespirationValue") is not None:
        out["low"] = round(data["lowestRespirationValue"], 1)
    if data.get("highestRespirationValue") is not None:
        out["high"] = round(data["highestRespirationValue"], 1)
    if data.get("awakeRespirationValue") is not None:
        out["awake"] = round(data["awakeRespirationValue"], 1)
    return out or None
