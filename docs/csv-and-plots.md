# CSV export

After `garmin-sync sync` has produced daily JSON files, you can flatten a range
of them into a single CSV for spreadsheet/Grafana/whatever-you-want use.

## Usage

```bash
# Using a profile (reads input_dir from profile.output_dir)
garmin-sync export-csv --profile me --start 2026-05-01 --end 2026-05-29 --out /tmp/me.csv

# Or pass the directory explicitly
garmin-sync export-csv --input-dir ~/garmin-data/me \
    --start 2026-05-01 --end 2026-05-29 --out /tmp/me.csv
```

## Schema

Column order is fixed; new metrics are appended at the end across releases so
existing sheets don't break. Header row:

```
date, sleep_score, sleep_total_min, sleep_deep_min, sleep_light_min, sleep_rem_min,
sleep_awake_min, sleep_avg_spo2, sleep_lowest_spo2, sleep_avg_respiration,
sleep_avg_stress, steps_total, steps_distance_km, steps_goal, hrv_weekly_avg_ms,
hrv_last_night_ms, hrv_status, hrv_5min_high_ms, hrv_baseline_low,
hrv_baseline_upper, spo2_avg_pct, spo2_min_pct, spo2_avg_hr_bpm,
body_battery_charged, body_battery_drained, body_battery_max, body_battery_min,
stress_overall, stress_level, stress_rest_min, stress_low_min, stress_medium_min,
stress_high_min, respiration_low, respiration_high, respiration_avg,
intensity_moderate_min, intensity_vigorous_min, intensity_weekly_goal_min,
training_readiness_score, training_readiness_status, resting_heart_rate,
vo2_max_running, vo2_max_cycling, activities_count
```

Missing values are written as empty strings, **not** as 0 or NaN, so downstream
tools can distinguish "no data" from "value was zero".

## Trend plots

Coming in v0.2 (batch 4).
