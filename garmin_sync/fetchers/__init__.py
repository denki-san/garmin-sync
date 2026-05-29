"""Per-metric fetchers. Each returns ``dict | None`` (pure data, no formatting)."""
from .sleep import fetch_sleep
from .body import fetch_steps, fetch_hrv, fetch_spo2
from .stress import fetch_stress
from .body_battery import fetch_body_battery
from .training_readiness import fetch_training_readiness
from .respiration import fetch_respiration
from .intensity import fetch_intensity
from .activities import fetch_activities
from .resting_heart_rate import fetch_resting_heart_rate
from .vo2_max import fetch_vo2_max
from .daily_summary import fetch_daily_summary

__all__ = [
    "fetch_sleep",
    "fetch_steps",
    "fetch_hrv",
    "fetch_spo2",
    "fetch_stress",
    "fetch_body_battery",
    "fetch_training_readiness",
    "fetch_respiration",
    "fetch_intensity",
    "fetch_activities",
    "fetch_resting_heart_rate",
    "fetch_vo2_max",
    "fetch_daily_summary",
]
