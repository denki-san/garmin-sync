# garminconnect password-login fallback

`garmin-sync` uses [`garminconnect`](https://github.com/cyberjunky/python-garminconnect)
to reach a small set of endpoints that garth's OAuth scope can't access. This
page documents what it adds, how it's configured, and the data-structure traps
to know.

## What needs it

| Endpoint | Method | Returns |
|---|---|---|
| `/userstats-service/wellness/daily/{user}` | `Garmin.get_rhr_day(day)` | Daily resting heart rate (and min/max HR) |
| `/metrics-service/metrics/maxmet/daily/{start}/{end}` | `Garmin.connectapi(url)` | VO2 Max — running & cycling |

Other endpoints (sleep, steps, HRV, Body Battery, etc.) work fine through
garth and don't need this fallback.

## Setup

```bash
# 1. Install garminconnect alongside garmin-sync
pip install garminconnect

# 2. Provide credentials. Either via your shell environment:
export GARMIN_PASSWORD='...'

# Or by appending to ~/.hermes/.env (garmin-sync reads this automatically):
echo 'GARMIN_PASSWORD=...' >> ~/.hermes/.env

# 3. The profile entry needs an email (or set GARMIN_EMAIL env var):
#    email = "you@example.com"
```

For multiple accounts on the same machine, set a distinct `password_env_var`
per profile:

```toml
[profiles.me]
email            = "you@example.com"
password_env_var = "GARMIN_PASSWORD"

[profiles.spouse]
email            = "spouse@example.com"
password_env_var = "SPOUSE_GARMIN_PASSWORD"
```

If `password_env_var` resolves to nothing, the RHR and VO2 Max fetchers
short-circuit silently and the resulting JSON omits those two keys. Other
metrics are unaffected.

## Resting heart rate — data structure

`garminconnect`'s `get_rhr_day()` returns a **nested** payload, not flat fields:

```json
{
  "allMetrics": {
    "metricsMap": {
      "WELLNESS_RESTING_HEART_RATE": [
        {"value": 55.0, "calendarDate": "2026-05-25"}
      ]
    }
  }
}
```

Wrong:

```python
rhr.get("restingHeartRate")   # always None
```

Right:

```python
items = rhr["allMetrics"]["metricsMap"]["WELLNESS_RESTING_HEART_RATE"]
value = items[-1]["value"]  # take the latest entry
```

Other metric keys that may appear:

- `WELLNESS_MIN_HEART_RATE`
- `WELLNESS_MAX_HEART_RATE`

Each is an array; take `[-1]` (newest).

## VO2 Max — data structure

`get_max_metrics("2026-05-25")` for a single day often returns `[]`. The
endpoint only emits a value on days the device computed one (typically after
a tagged run/ride). The workaround is to query a wider date range and pick
the last entry:

```python
# Note the doubled date: the endpoint is /maxmet/daily/{start}/{end}
url = f"{gc.garmin_connect_metrics_url}/2026-01-01/2026-05-25"
vo2 = gc.connectapi(url)
```

Response shape:

```json
[
  {
    "generic": {
      "calendarDate": "2026-05-16",
      "vo2MaxValue": 43.0,
      "vo2MaxPreciseValue": 42.5,
      "fitnessAge": null
    },
    "cycling": {"vo2MaxValue": null}
  }
]
```

Wrong:

```python
item = vo2  # TypeError — it's a list
val = item["vo2MaxValue"]  # KeyError — the value is nested under "generic"
```

Right:

```python
for item in vo2:
    gen = item.get("generic", {})
    running = gen.get("vo2MaxValue")
    running_precise = gen.get("vo2MaxPreciseValue")
    cycling = (item.get("cycling") or {}).get("vo2MaxValue")
```

## Session reuse and conflict notes

Internally `garminconnect` builds on `garth` — it just re-logs in with the
password to obtain a wider-scope token instead of the cached web-embed one.
`garmin-sync` caches one `Garmin` client per `(email, domain)` for the
duration of a `sync` run, so you pay the login cost once per invocation.

The garth SSO session (used for sleep/steps/etc.) and the garminconnect
session are independent objects, so they don't trample each other's cookies.

## When the fallback isn't worth it

If you don't track running/cycling regularly, VO2 Max won't update and the
extra login is wasted. Leave `password_env_var` unset and those two keys
simply won't appear in the JSON output.

For RHR specifically, some Garmin devices write a "summary RHR" to the regular
wellness endpoints — if that field shows up in your existing JSON under
another path, you may not need the fallback at all. (`garmin-sync` does not
currently parse that path.)
