"""Sleep score + detailed stages + during-sleep SpO2/respiration."""
from __future__ import annotations

import logging
from datetime import datetime, timezone

log = logging.getLogger("garmin_sync.fetch.sleep")


def _ts_to_local_str(ms: int | None) -> str | None:
    """Garmin's ``...TimestampLocal`` field is epoch-ms already shifted to local."""
    if ms is None:
        return None
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc).strftime("%Y-%m-%d %H:%M")


def fetch_sleep(gc, day: str) -> dict | None:
    try:
        sleep_data = gc.get_sleep_data(day)
    except Exception as e:
        log.debug("sleep fetch failed: %s", e)
        return None
    if not sleep_data:
        return None
    dto = sleep_data.get("dailySleepDTO") or {}
    if not dto:
        return None

    out: dict = {}

    scores = dto.get("sleepScores") or {}
    overall = scores.get("overall") or {}
    if overall.get("value") is not None:
        out["score"] = overall["value"]

    if dto.get("sleepStartTimestampLocal"):
        out["start"] = _ts_to_local_str(dto["sleepStartTimestampLocal"])
    if dto.get("sleepEndTimestampLocal"):
        out["end"] = _ts_to_local_str(dto["sleepEndTimestampLocal"])

    total_sec = dto.get("sleepTimeSeconds")
    stage_entry: dict = {}
    if total_sec:
        stage_entry["total_min"] = total_sec // 60
        if dto.get("deepSleepSeconds"):
            stage_entry["deep_min"] = dto["deepSleepSeconds"] // 60
        if dto.get("lightSleepSeconds"):
            stage_entry["light_min"] = dto["lightSleepSeconds"] // 60
        if dto.get("remSleepSeconds"):
            stage_entry["rem_min"] = dto["remSleepSeconds"] // 60
        if dto.get("awakeSleepSeconds"):
            stage_entry["awake_min"] = dto["awakeSleepSeconds"] // 60
        nap = dto.get("napTimeSeconds") or 0
        if nap:
            stage_entry["nap_min"] = nap // 60

        if dto.get("averageSpO2Value") is not None:
            stage_entry["avg_spo2"] = dto["averageSpO2Value"]
            if dto.get("lowestSpO2Value") is not None:
                stage_entry["lowest_spo2"] = dto["lowestSpO2Value"]
            if dto.get("averageSpO2HRSleep") is not None:
                stage_entry["avg_spo2_hr"] = round(dto["averageSpO2HRSleep"], 1)
        if dto.get("averageRespirationValue") is not None:
            stage_entry["avg_respiration"] = round(dto["averageRespirationValue"], 1)
            if dto.get("lowestRespirationValue") is not None:
                stage_entry["lowest_respiration"] = round(dto["lowestRespirationValue"], 1)
        if dto.get("avgSleepStress") is not None:
            stage_entry["avg_sleep_stress"] = round(dto["avgSleepStress"], 1)

    if stage_entry:
        out["stages"] = stage_entry
    return out or None
