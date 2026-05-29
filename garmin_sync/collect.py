"""Aggregate all per-metric fetchers into one ``dict`` per day.

The output schema matches the JSON files written by the personal ``garmin-cn``
skill, so the downstream Chinese-emoji renderer in that skill can keep working
without changes.
"""
from __future__ import annotations

import logging

from .auth import get_garminconnect_client
from .fetchers import (
    fetch_activities,
    fetch_body_battery,
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
from .profile import Profile

log = logging.getLogger("garmin_sync.collect")


def collect_day(client, day: str, profile: Profile | None = None) -> dict:
    """Return a single dict matching the JSON schema written by garmin-cn.

    The garth ``client`` covers everything except RHR / VO2 Max, which need a
    garminconnect password-login client. When ``profile`` is supplied we look
    one up lazily from the env. If unavailable, those two keys are simply absent.
    """
    data: dict = {"date": day}

    try:
        prof = client.get_basic_profile_data()
        if prof and prof.get("displayName"):
            data["display_name"] = prof["displayName"]
    except Exception:
        pass

    sleep = fetch_sleep(client, day)
    if sleep:
        data["sleep"] = sleep

    steps = fetch_steps(client, day)
    if steps:
        data["steps"] = steps

    hrv = fetch_hrv(client, day)
    if hrv:
        data["hrv"] = hrv

    spo2 = fetch_spo2(client, day)
    if spo2:
        data["spo2"] = spo2

    bb = fetch_body_battery(client, day)
    if bb:
        data["body_battery"] = bb

    if profile is not None:
        gc = get_garminconnect_client(profile)
        rhr = fetch_resting_heart_rate(gc, day)
        if rhr:
            data["resting_heart_rate"] = rhr
        vo2 = fetch_vo2_max(gc, day)
        if vo2:
            data["vo2_max"] = vo2

    tr = fetch_training_readiness(client, day)
    if tr:
        data["training_readiness"] = tr

    stress = fetch_stress(client, day)
    if stress:
        data["stress"] = stress

    resp = fetch_respiration(client, day)
    if resp:
        data["respiration"] = resp

    im = fetch_intensity(client, day)
    if im:
        data["intensity_minutes"] = im

    acts = fetch_activities(client, day)
    if acts:
        data["activities"] = acts

    return data
