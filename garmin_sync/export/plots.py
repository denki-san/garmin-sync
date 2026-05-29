"""Lightweight matplotlib trend plots from previously-synced JSON files.

Imported lazily so the base install doesn't pull matplotlib unless requested
(install via ``pip install garmin-sync[plots]``).
"""
from __future__ import annotations

import logging
from datetime import date as _date, datetime, timedelta
from math import isnan, nan
from pathlib import Path

from ..storage import read_day_json

log = logging.getLogger("garmin_sync.export.plots")


# metric key → (display label, JSON extractor)
METRIC_EXTRACTORS: dict[str, tuple[str, callable]] = {
    "hrv": ("HRV (ms, last night)",
            lambda d: (d.get("hrv") or {}).get("last_night_ms")),
    "hrv_5min_high": ("HRV 5-min high (ms)",
                      lambda d: (d.get("hrv") or {}).get("last_night_5_min_high_ms")),
    "sleep_score": ("Sleep score",
                    lambda d: (d.get("sleep") or {}).get("score")),
    "sleep_total_min": ("Sleep total (min)",
                        lambda d: ((d.get("sleep") or {}).get("stages") or {}).get("total_min")),
    "steps": ("Daily steps",
              lambda d: (d.get("steps") or {}).get("total")),
    "body_battery_min": ("Body Battery (daily min)",
                         lambda d: (d.get("body_battery") or {}).get("min")),
    "body_battery_max": ("Body Battery (daily max)",
                         lambda d: (d.get("body_battery") or {}).get("max")),
    "stress_overall": ("Stress (0–100)",
                       lambda d: (d.get("stress") or {}).get("overall")),
    "rhr": ("Resting HR (bpm)",
            lambda d: (d.get("resting_heart_rate") or {}).get("value")),
    "vo2_max_running": ("VO2 Max — running",
                        lambda d: (d.get("vo2_max") or {}).get("running")),
}


def list_metrics() -> list[str]:
    return sorted(METRIC_EXTRACTORS.keys())


def _date_range(end: _date, days: int) -> list[_date]:
    return [end - timedelta(days=days - 1 - i) for i in range(days)]


def _rolling_mean(values: list[float], window: int) -> list[float]:
    """Centered rolling mean ignoring NaNs. Returns NaN if window fully empty."""
    n = len(values)
    out: list[float] = [nan] * n
    half = window // 2
    for i in range(n):
        lo = max(0, i - half)
        hi = min(n, i + half + 1)
        chunk = [v for v in values[lo:hi] if not (isinstance(v, float) and isnan(v))]
        if chunk:
            out[i] = sum(chunk) / len(chunk)
    return out


def plot_metric(
    input_dir: Path,
    metric: str,
    days: int,
    out_path: Path,
    *,
    end_date: str | None = None,
    rolling_window: int = 7,
    title: str | None = None,
) -> Path:
    """Write a PNG showing ``metric`` over the last ``days`` ending at ``end_date``."""
    if metric not in METRIC_EXTRACTORS:
        raise ValueError(
            f"Unknown metric {metric!r}. Available: {', '.join(list_metrics())}"
        )

    end = _date.fromisoformat(end_date) if end_date else (_date.today() - timedelta(days=1))
    if days < 2:
        raise ValueError("days must be >= 2 for a meaningful trend")

    label, extractor = METRIC_EXTRACTORS[metric]
    dates = _date_range(end, days)
    values: list[float] = []
    for d in dates:
        data = read_day_json(Path(input_dir).expanduser(), d.strftime("%Y-%m-%d"))
        v = extractor(data) if data else None
        values.append(float(v) if v is not None else nan)

    # Refuse to plot if literally nothing is there
    if all(isinstance(v, float) and isnan(v) for v in values):
        raise ValueError(
            f"No '{metric}' values found in {input_dir} for "
            f"{dates[0].isoformat()}..{dates[-1].isoformat()}"
        )

    # Lazy import so the dependency only matters when plotting
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates

    fig, ax = plt.subplots(figsize=(10, 4.5))
    xs = [datetime.combine(d, datetime.min.time()) for d in dates]

    ax.plot(xs, values, marker="o", markersize=3.5, linewidth=1.4,
            label=label, color="#1f77b4")

    if days >= rolling_window:
        smoothed = _rolling_mean(values, rolling_window)
        ax.plot(xs, smoothed, linestyle="--", linewidth=1.2,
                label=f"{rolling_window}-day rolling mean", color="#d62728")

    ax.set_title(title or f"{label} — last {days} days")
    ax.set_xlabel("Date")
    ax.set_ylabel(label)
    ax.grid(True, alpha=0.3)
    ax.legend(loc="best", fontsize=9)

    # Sensible date locator: ~every 7 days for ranges > 30, else daily
    locator = mdates.DayLocator(interval=max(1, days // 10))
    ax.xaxis.set_major_locator(locator)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%m-%d"))
    fig.autofmt_xdate(rotation=30)

    fig.tight_layout()
    out_path = Path(out_path).expanduser()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=120)
    plt.close(fig)
    return out_path
