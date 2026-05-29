"""Resting heart rate via garminconnect password-login (garth scope 403)."""
from __future__ import annotations

import logging

log = logging.getLogger("garmin_sync.fetch.rhr")


def fetch_resting_heart_rate(gc_client, day: str) -> dict | None:
    """Requires a garminconnect ``Garmin`` client (NOT garth). Returns None if unavailable."""
    if gc_client is None:
        return None
    try:
        rhr = gc_client.get_rhr_day(day)
        if not rhr:
            return None
        metrics = rhr.get("allMetrics", {}).get("metricsMap", {})
        out: dict = {}
        if "WELLNESS_RESTING_HEART_RATE" in metrics and metrics["WELLNESS_RESTING_HEART_RATE"]:
            val = metrics["WELLNESS_RESTING_HEART_RATE"][-1].get("value")
            if val is not None:
                out["value"] = val
        for metric_key in ("WELLNESS_MIN_HEART_RATE", "WELLNESS_MAX_HEART_RATE"):
            if metric_key in metrics and metrics[metric_key]:
                val = metrics[metric_key][-1].get("value")
                if val is not None:
                    out[metric_key] = val
        return out or None
    except Exception as e:
        log.debug("rhr fetch failed: %s", e)
        return None
