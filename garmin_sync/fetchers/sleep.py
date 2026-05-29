"""Sleep score + detailed stages + during-sleep SpO2/respiration/HR."""
from __future__ import annotations

import logging
from datetime import date as _date

log = logging.getLogger("garmin_sync.fetch.sleep")


def fetch_sleep(client, day: str) -> dict | None:
    """Return the same JSON structure that garmin-cn writes under ``sleep``:

    {
        "score": int,
        "start": "YYYY-MM-DD HH:MM",
        "end": "YYYY-MM-DD HH:MM",
        "stages": {
            "total_min": ..., "deep_min": ..., "light_min": ..., "rem_min": ...,
            "awake_min": ..., "nap_min": ...,
            "avg_spo2": ..., "lowest_spo2": ..., "avg_spo2_hr": ...,
            "avg_respiration": ..., "lowest_respiration": ...,
            "avg_sleep_stress": ...,
        }
    }
    """
    from garth.data.sleep import SleepData

    score: int | None = None
    sleep_start_str: str | None = None
    sleep_end_str: str | None = None
    stage_entry: dict = {}

    try:
        sleep_data = SleepData.get(day, client=client)
        if not sleep_data:
            return _score_only_fallback(client, day)
        dto = sleep_data.daily_sleep_dto

        if dto.sleep_scores and dto.sleep_scores.overall:
            score = dto.sleep_scores.overall.value
        if score is None:
            from garth.stats.sleep import DailySleep as StatsDailySleep
            sl = StatsDailySleep.list(end=_date.fromisoformat(day), period=1, client=client)
            if sl and sl[0].value is not None:
                score = sl[0].value

        total_sec = dto.sleep_time_seconds
        if total_sec:
            sleep_start_str = str(dto.sleep_start)[:16] if dto.sleep_start else None
            sleep_end_str = str(dto.sleep_end)[:16] if dto.sleep_end else None
            stage_entry["total_min"] = total_sec // 60
            if dto.deep_sleep_seconds:
                stage_entry["deep_min"] = dto.deep_sleep_seconds // 60
            if dto.light_sleep_seconds:
                stage_entry["light_min"] = dto.light_sleep_seconds // 60
            if dto.rem_sleep_seconds:
                stage_entry["rem_min"] = dto.rem_sleep_seconds // 60
            if dto.awake_sleep_seconds:
                stage_entry["awake_min"] = dto.awake_sleep_seconds // 60
            nap = dto.nap_time_seconds or 0
            if nap:
                stage_entry["nap_min"] = nap // 60

            if dto.average_sp_o2_value is not None:
                stage_entry["avg_spo2"] = dto.average_sp_o2_value
                if dto.lowest_sp_o2_value is not None:
                    stage_entry["lowest_spo2"] = dto.lowest_sp_o2_value
                if dto.average_sp_o2_hr_sleep is not None:
                    stage_entry["avg_spo2_hr"] = round(dto.average_sp_o2_hr_sleep, 1)
            if dto.average_respiration_value is not None:
                stage_entry["avg_respiration"] = round(dto.average_respiration_value, 1)
                if dto.lowest_respiration_value is not None:
                    stage_entry["lowest_respiration"] = round(dto.lowest_respiration_value, 1)
            if dto.avg_sleep_stress is not None:
                stage_entry["avg_sleep_stress"] = round(dto.avg_sleep_stress, 1)
    except Exception as e:
        log.debug("sleep detailed fetch failed: %s", e)
        return _score_only_fallback(client, day)

    if not stage_entry and score is None:
        return None

    out: dict = {}
    if score is not None:
        out["score"] = score
    if sleep_start_str:
        out["start"] = sleep_start_str
    if sleep_end_str:
        out["end"] = sleep_end_str
    if stage_entry:
        out["stages"] = stage_entry
    return out or None


def _score_only_fallback(client, day: str) -> dict | None:
    from garth.stats.sleep import DailySleep as StatsDailySleep

    try:
        sl = StatsDailySleep.list(end=_date.fromisoformat(day), period=1, client=client)
        if sl and sl[0].value is not None:
            return {"score": sl[0].value}
    except Exception as e:
        log.debug("sleep score fallback failed: %s", e)
    return None
