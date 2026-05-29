# Garmin Connect API endpoints used by garmin-sync

Quick reference of the endpoints each fetcher hits. Useful when diagnosing
missing data or extending coverage. All calls go through one
`garminconnect.Garmin` session per profile.

> **Domain caveat**: `garmin.com` and `garmin.cn` share `/wellness-service/*`
> backends, but Body Battery, Training Readiness, VO2 Max, and dailyHeartRate
> **404 on garmin.cn** even with a valid token. CN accounts that need those
> metrics have to migrate the account region (Garmin support can do it).

## Per-fetcher endpoint map

| Fetcher | garminconnect call | HTTP endpoint |
|---|---|---|
| `sleep` | `Garmin.get_sleep_data(day)` | `/wellness-service/wellness/dailySleepData/{user}?date=...` |
| `steps` | `Garmin.get_daily_steps(day, day)` | `/usersummary-service/stats/steps/daily/{start}/{end}` |
| `hrv` | `Garmin.get_hrv_data(day)` | `/hrv-service/hrv/{day}` |
| `spo2` | `Garmin.connectapi(...)` | `/wellness-service/wellness/dailySpo2/{day}` |
| `body_battery` | `Garmin.connectapi(..., params={startDate, endDate})` | `/wellness-service/wellness/bodyBattery/reports/daily` |
| `stress` | `Garmin.connectapi(...)` | `/usersummary-service/stats/stress/daily/{start}/{end}` |
| `respiration` | `Garmin.connectapi(...)` | `/wellness-service/wellness/daily/respiration/{day}` |
| `intensity_minutes` | `Garmin.get_intensity_minutes_data(day)` | `/usersummary-service/usersummary/im/daily/{user}` |
| `training_readiness` | `Garmin.connectapi(...)` | `/metrics-service/metrics/trainingreadiness/{day}` |
| `activities` | `Garmin.connectapi(...)` | `/activitylist-service/activities/search/activities?startDate&endDate` |
| `resting_heart_rate` | `Garmin.get_rhr_day(day)` | `/userstats-service/wellness/daily/{user}` |
| `vo2_max` | `Garmin.connectapi(...)` | `/metrics-service/metrics/maxmet/daily/{start}/{end}` |

## JSON-schema field mapping

The fetchers normalise the raw camelCase Garmin response into the snake_case
schema documented in [`../README.md`](../README.md). Highlights:

| Our JSON path | Source field |
|---|---|
| `sleep.score` | `dailySleepDTO.sleepScores.overall.value` |
| `sleep.stages.{total,deep,light,rem,awake}_min` | `dailySleepDTO.{...}SleepSeconds // 60` |
| `sleep.stages.avg_spo2` | `dailySleepDTO.averageSpO2Value` |
| `steps.distance_km` | `totalDistance / 1000` (raw is metres, rounded to 3 dp) |
| `hrv.{weekly_avg_ms, last_night_ms}` | `hrvSummary.{weeklyAvg, lastNightAvg}` |
| `hrv.baseline.{balanced_low, balanced_upper, marker_value}` | `hrvSummary.baseline.{balancedLow, balancedUpper, markerValue}` |
| `stress.{rest,low,medium,high}_min` | `values.{rest,low,medium,high}StressDuration / 60` |
| `body_battery.{max, min}` | computed from `bodyBatteryValuesArray` |
| `intensity_minutes.moderate_min` | `moderateMinutes` (NOT `weeklyModerate`, which is the rolling sum) |
| `resting_heart_rate.value` | `allMetrics.metricsMap.WELLNESS_RESTING_HEART_RATE[-1].value` |
| `vo2_max.{running, cycling}` | `generic.vo2MaxValue`, `cycling.vo2MaxValue` (loop over the list) |

## Gotchas

- **VO2 Max single-day usually returns `[]`** — the metric only updates after a tagged run/ride. The fetcher transparently widens to a 1-year range and takes the latest.
- **Body Battery field names are `charged` / `drained`** — *not* `bodyBatteryChargeValue` / `bodyBatteryDrainValue` (a common documentation error).
- **Stress bucket durations** live on `/usersummary-service/stats/stress/daily/...`, not on the per-3-min `/wellness-service/wellness/dailyStress/...` endpoint that `Garmin.get_stress_data` calls. The fetcher hits the usersummary path directly.
- **`Garmin.get_spo2_data(day)` strips the `averageSpO2HR` field** present on the underlying `/wellness-service/wellness/dailySpo2/{day}` response. The fetcher calls `connectapi` directly to keep the field.
