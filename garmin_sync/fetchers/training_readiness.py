"""Training readiness via /metrics-service/metrics/trainingreadiness/{date}."""
from __future__ import annotations

import logging

log = logging.getLogger("garmin_sync.fetch.training_readiness")


def fetch_training_readiness(gc, day: str) -> dict | None:
    try:
        data = gc.connectapi(f"/metrics-service/metrics/trainingreadiness/{day}")
    except Exception as e:
        log.debug("training readiness fetch failed: %s", e)
        return None
    if not data:
        return None
    # API returns a list (one entry per device that reported). Take the most recent.
    if isinstance(data, list):
        if not data:
            return None
        data = data[-1]
    out: dict = {}
    if data.get("overall") is not None:
        out["score"] = data["overall"]
    factors = data.get("factors") or {}
    for fk, fv in factors.items():
        if isinstance(fv, dict) and fv.get("value") is not None:
            out[fk] = fv["value"]
    if data.get("status"):
        out["status"] = data["status"]
    return out or None
