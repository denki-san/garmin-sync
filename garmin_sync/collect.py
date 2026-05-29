"""Aggregate all per-metric fetchers into one ``dict`` per day.

All fetchers accept the same ``garminconnect.Garmin`` client; the JSON schema
matches what the personal ``garmin-cn`` skill writes so the downstream
Chinese-emoji renderer keeps working without changes.
"""
from __future__ import annotations

import logging

from .fetchers import (
    fetch_activities,
    fetch_body_battery,
    fetch_daily_summary,
    fetch_hrv,
    fetch_intensity,
    fetch_resting_heart_rate,
    fetch_respiration,
    fetch_sleep,
    fetch_spo2,
    fetch_steps,
    fetch_stress,
    fetch_training_readiness,
    fetch_vo2_max,
)

log = logging.getLogger("garmin_sync.collect")


def collect_day(gc, day: str) -> dict:
    """Return one dict matching the JSON schema written under ``output_dir``.

    ``gc`` is an authenticated :class:`garminconnect.Garmin` instance (typically
    from :func:`garmin_sync.auth.authenticate`).
    """
    data: dict = {"date": day}

    try:
        display_name = gc.get_full_name()
        if display_name:
            data["display_name"] = display_name
    except Exception:
        pass

    sleep = fetch_sleep(gc, day)
    if sleep:
        data["sleep"] = sleep

    steps = fetch_steps(gc, day)
    if steps:
        data["steps"] = steps

    hrv = fetch_hrv(gc, day)
    if hrv:
        data["hrv"] = hrv

    spo2 = fetch_spo2(gc, day)
    if spo2:
        data["spo2"] = spo2

    bb = fetch_body_battery(gc, day)
    if bb:
        data["body_battery"] = bb

    rhr = fetch_resting_heart_rate(gc, day)
    if rhr:
        data["resting_heart_rate"] = rhr

    # One call → heart_rate / calories / floors / activity_seconds (merged at top level)
    daily = fetch_daily_summary(gc, day)
    if daily:
        data.update(daily)

    vo2 = fetch_vo2_max(gc, day)
    if vo2:
        data["vo2_max"] = vo2

    tr = fetch_training_readiness(gc, day)
    if tr:
        data["training_readiness"] = tr

    stress = fetch_stress(gc, day)
    if stress:
        data["stress"] = stress

    resp = fetch_respiration(gc, day)
    if resp:
        data["respiration"] = resp

    im = fetch_intensity(gc, day)
    if im:
        data["intensity_minutes"] = im

    acts = fetch_activities(gc, day)
    if acts:
        data["activities"] = acts

    return data
