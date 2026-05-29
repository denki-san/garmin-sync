"""Smoke tests for export.plots — skipped if matplotlib not installed."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

pytest.importorskip("matplotlib")

from garmin_sync.export.plots import (  # noqa: E402
    METRIC_EXTRACTORS,
    _rolling_mean,
    list_metrics,
    plot_metric,
)


def _write(d: Path, day: str, payload: dict) -> None:
    d.mkdir(parents=True, exist_ok=True)
    (d / f"{day}.json").write_text(json.dumps({"date": day, **payload}), encoding="utf-8")


def test_list_metrics_contains_core_keys():
    keys = list_metrics()
    for k in ("hrv", "sleep_score", "steps", "rhr", "stress_overall"):
        assert k in keys


def test_rolling_mean_ignores_nan_and_centers():
    from math import nan, isnan
    vals = [1.0, nan, 3.0, nan, 5.0]
    out = _rolling_mean(vals, 3)
    # center=0: [1] -> 1.0; center=1: [1,3] -> 2.0; center=2: [3] -> 3.0; center=3: [3,5] -> 4.0; center=4: [5] -> 5.0
    assert out[0] == 1.0
    assert out[1] == 2.0
    assert out[2] == 3.0
    assert out[3] == 4.0
    assert out[4] == 5.0
    # All-nan window
    assert isnan(_rolling_mean([nan, nan], 3)[0])


def test_plot_metric_writes_png(tmp_path):
    in_dir = tmp_path / "data"
    for i, day in enumerate(["2026-05-10", "2026-05-11", "2026-05-12", "2026-05-13", "2026-05-14"]):
        _write(in_dir, day, {"hrv": {"last_night_ms": 40 + i}})
    out = tmp_path / "hrv.png"
    plot_metric(in_dir, "hrv", days=5, out_path=out, end_date="2026-05-14")
    assert out.exists()
    with open(out, "rb") as f:
        header = f.read(8)
    assert header[:8] == b"\x89PNG\r\n\x1a\n", "output is not a PNG"


def test_plot_metric_handles_gaps(tmp_path):
    in_dir = tmp_path / "data"
    # 5 days, only days 1 and 4 present
    _write(in_dir, "2026-05-10", {"steps": {"total": 1000}})
    _write(in_dir, "2026-05-13", {"steps": {"total": 4000}})
    out = tmp_path / "steps.png"
    plot_metric(in_dir, "steps", days=5, out_path=out, end_date="2026-05-14")
    assert out.exists()


def test_plot_metric_rejects_unknown_metric(tmp_path):
    with pytest.raises(ValueError, match="Unknown metric"):
        plot_metric(tmp_path, "bogus", days=10, out_path=tmp_path / "x.png", end_date="2026-05-14")


def test_plot_metric_rejects_empty_range(tmp_path):
    # No data files at all
    with pytest.raises(ValueError, match="No 'hrv' values"):
        plot_metric(tmp_path, "hrv", days=5, out_path=tmp_path / "x.png", end_date="2026-05-14")
