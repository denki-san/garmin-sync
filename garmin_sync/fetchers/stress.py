"""Daily stress (overall 0-100 + buckets)."""
from __future__ import annotations

import logging
from datetime import date as _date

log = logging.getLogger("garmin_sync.fetch.stress")


# garmin-cn historically labeled buckets in Chinese; keep ASCII label here and
# let downstream renderers translate. The thresholds match the original script.
def _bucket(overall: int) -> str:
    if overall < 20:
        return "放松"
    if overall < 40:
        return "低"
    if overall < 60:
        return "中"
    if overall < 80:
        return "高"
    return "极高"


def fetch_stress(client, day: str) -> dict | None:
    from garth.stats.stress import DailyStress

    try:
        stress_list = DailyStress.list(end=_date.fromisoformat(day), period=1, client=client)
        if not stress_list:
            return None
        s = stress_list[0]
        if s.overall_stress_level is None:
            return None
        out: dict = {
            "overall": s.overall_stress_level,
            "level": _bucket(s.overall_stress_level),
        }
        if s.rest_stress_duration is not None:
            out["rest_min"] = round(s.rest_stress_duration / 60)
        if s.low_stress_duration is not None:
            out["low_min"] = round(s.low_stress_duration / 60)
        if s.medium_stress_duration is not None:
            out["medium_min"] = round(s.medium_stress_duration / 60)
        if s.high_stress_duration is not None:
            out["high_min"] = round(s.high_stress_duration / 60)
        return out
    except Exception as e:
        log.debug("stress fetch failed: %s", e)
        return None
