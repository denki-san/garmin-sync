# Garmin Connect API endpoints used by garmin-sync

This is a quick reference of the endpoints each fetcher hits. Useful when
diagnosing missing data or extending coverage.

> **Domain caveat**: `garmin.com` and `garmin.cn` share `/wellness-service/*`
> backends, but most "advanced" metrics (Body Battery, Resting HR, VO2 Max,
> Training Readiness, dailyHeartRate) **404 on garmin.cn** even with a valid
> token. If you have a CN account that needs these metrics, see
> [`migration-cn-to-com.md`](migration-cn-to-com.md) (not yet written).

## garth stats modules (both domains)

```python
from datetime import date
from garth.stats.steps import DailySteps
from garth.stats.stress import DailyStress
from garth.stats.hrv import DailyHRV
from garth.stats.intensity_minutes import DailyIntensityMinutes

# Single day
steps  = DailySteps.list(end=date.today(), period=1, client=client)
stress = DailyStress.list(end=date.today(), period=1, client=client)
hrv    = DailyHRV.list(end=date.today(), period=1, client=client)
im     = DailyIntensityMinutes.list(end=date.today(), period=1, client=client)
```

| Module | Fields used by garmin-sync |
|---|---|
| `DailySteps` | `total_steps`, `total_distance` (m), `step_goal` |
| `DailyStress` | `overall_stress_level` (0–100), `rest/low/medium/high_stress_duration` (s) |
| `DailyHRV` | `weekly_avg`, `last_night_avg`, `last_night_5_min_high`, `baseline.{balanced_low, balanced_upper, marker_value}`, `status`, `feedback_phrase` |
| `DailyIntensityMinutes` | `moderate_value`, `vigorous_value`, `weekly_goal` |

## SleepData (detailed stages)

```python
from garth.data.sleep import SleepData
sd = SleepData.get("2026-05-15", client=client)  # day must be a "YYYY-MM-DD" str
dto = sd.daily_sleep_dto
```

Fields read:

- Duration: `sleep_time_seconds`, `deep/light/rem/awake_sleep_seconds`, `nap_time_seconds`
- Boundaries: `sleep_start`, `sleep_end` (datetime)
- Sleep-window SpO2: `average_sp_o2_value`, `lowest_sp_o2_value`, `average_sp_o2_hr_sleep`
- Sleep-window respiration: `average_respiration_value`, `lowest_respiration_value`
- Sleep score: `sleep_scores.overall.value` (with `DailySleep.list` as fallback)

## Direct connectapi endpoints

All hit via `client.connectapi(path)` on the garth client.

| Endpoint | Returns | Notes |
|---|---|---|
| `/wellness-service/wellness/dailySpo2/{day}` | `averageSpO2`, `lowestSpO2`, `averageSpO2HR` | Daytime SpO2, distinct from sleep-window SpO2 |
| `/wellness-service/wellness/bodyBattery/reports/daily?startDate&endDate` | List of `{charged, drained, bodyBatteryValuesArray}` | Field names are `charged`/`drained`, NOT `bodyBatteryChargeValue` |
| `/wellness-service/wellness/daily/respiration/{day}` | `averageRespirationValue`, `lowest`, `highest`, `awake` | |
| `/metrics-service/metrics/trainingreadiness/{day}` | `overall` score + per-factor map + status | |
| `/activitylist-service/activities/search/activities?startDate={day}&endDate={day}` | List of activities | Per-activity `activityName`, `duration`, `distance`, `calories`, `startTimeLocal` |

## garth scope limits (requires garminconnect fallback)

These endpoints return `403` with garth's OAuth scope. The package falls back
to `garminconnect` password login when `GARMIN_PASSWORD` is set (or available
in the configured `password_env_var` / `~/.hermes/.env`).

| Endpoint | Provided by | Notes |
|---|---|---|
| `/userstats-service/wellness/daily/{user}` (Resting HR) | `garminconnect.Garmin.get_rhr_day` | Returns nested `allMetrics.metricsMap.WELLNESS_RESTING_HEART_RATE` |
| `/metrics-service/metrics/maxmet/daily/{start}/{end}` (VO2 Max) | `garminconnect.connectapi(...)` | **Single-day queries return `[]`**; we widen to 1-year range |

See [`garminconnect-fallback.md`](garminconnect-fallback.md) for setup and data
structure details.
