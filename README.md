# garmin-sync

> Sync Garmin Connect health data to local JSON files. Designed for
> LLM-driven analysis (Claude Code, Codex, Hermes, ChatGPT, etc.).

[English](./README.md) · [简体中文](./README.zh-CN.md)

`garmin-sync` is a small Python CLI + library that pulls each day's health
metrics from your Garmin account and writes them to disk as structured JSON.
There's no daemon, no third-party server, no cloud — just a script and a
folder of files your AI assistant (or your own scripts) can read.

```bash
pip install garmin-sync          # core
pip install 'garmin-sync[plots]' # add matplotlib trend plots
```

## Why this exists

The Garmin Connect mobile app is fine for a quick glance, but you can't ask
it questions like "how has my HRV trended against my sleep score over the
last month?" or "did my Body Battery debt correlate with the headache I had
on Thursday?" — those are LLM-shaped questions.

`garmin-sync` is the boring plumbing that gets your data out of Garmin and
into a format AI assistants can chew on. Once a day's JSON is on disk,
everything else (analysis, reports, alerts, plots) is just reading files.

### Comparison with adjacent projects

|   | garmin-sync | [nftechie/garmin-skill](https://github.com/nftechie/garmin-skill) | [arpanghosh8453/garmin-grafana](https://github.com/arpanghosh8453/garmin-grafana) |
|---|---|---|---|
| Architecture | Python → local JSON | Hosted SaaS (Transition) | Docker + InfluxDB + Grafana |
| Data ownership | Fully local | On Transition's servers | Local Docker volume |
| Ops cost | `pip install` + cron | API key | Docker stack |
| LLM-ready output | ✅ JSON + (optional) Markdown | ❌ AI-coach chat only | ❌ Grafana dashboards |
| `garmin.cn` support | ✅ | unverified | ✅ |
| Visualization | Lightweight matplotlib | — | Full Grafana |
| Offline | ✅ | ❌ | ✅ |

## Quick start

### 1. One-time authorization

```bash
garmin-sync setup --domain garmin.com --email you@example.com
# (you'll be prompted for password; or set $GARMIN_PASSWORD)
```

This caches OAuth tokens under `~/.garminconnect-garmin_com/` (or the
`token_dir` you configured). Re-run roughly once a year when tokens expire.

> 2FA accounts: garth's SSO flow doesn't currently handle MFA. Disable 2FA
> on your Garmin account during the one-time setup, then re-enable it. See
> [`docs/auth-troubleshooting.md`](docs/auth-troubleshooting.md).

### 2. Daily sync

```bash
# Sync yesterday's data
garmin-sync sync --domain garmin.com --days 1

# Backfill the last 30 days
garmin-sync sync --domain garmin.com --days 30

# A single specific day
garmin-sync sync --domain garmin.com --date 2026-05-15
```

By default JSON files land in `./health/`. Override with `--output-dir`.

### 3. (Optional) Configure profiles

`~/.config/garmin-sync/profiles.toml`:

```toml
[profiles.me]
email      = "you@example.com"
domain     = "garmin.com"
token_dir  = "~/.garminconnect-garmin_com"
output_dir = "~/garmin-data/me"

[profiles.spouse]
email            = "spouse@example.com"
domain           = "garmin.cn"
token_dir        = "~/.garminconnect-spouse-cn"
output_dir       = "~/garmin-data/spouse"
password_env_var = "SPOUSE_GARMIN_PASSWORD"
```

Then everything gets shorter:

```bash
garmin-sync setup --profile me --email you@example.com
garmin-sync sync  --profile me --days 1
```

Full details: [`docs/multi-user.md`](docs/multi-user.md).

## What gets synced

Each day is one JSON file like `2026-05-28.json`:

```json
{
  "date": "2026-05-28",
  "sleep": {
    "score": 88,
    "start": "2026-05-28 00:56",
    "end": "2026-05-28 08:30",
    "stages": {
      "total_min": 450, "deep_min": 114, "light_min": 272, "rem_min": 64,
      "awake_min": 4, "avg_respiration": 12.0, "avg_sleep_stress": 10.0
    }
  },
  "steps": {"total": 8833, "distance_km": 7.269, "goal": 7540},
  "hrv": {
    "weekly_avg_ms": 47, "last_night_ms": 46, "status": "BALANCED",
    "last_night_5_min_high_ms": 61,
    "baseline": {"balanced_low": 39, "balanced_upper": 51, "marker_value": 0.58},
    "feedback_phrase": "HRV_BALANCED_6"
  },
  "spo2":           {"avg_pct": 93.0, "min_pct": 86, "avg_hr_bpm": 60.0},
  "body_battery":   {"charged": 86, "drained": 92, "max": 99, "min": 7},
  "stress":         {"overall": 43, "level": "中", "rest_min": 494, ...},
  "respiration":    {"low": 9.0, "high": 22.0},
  "intensity_minutes": {"moderate_min": 3, "vigorous_min": 0, "weekly_goal_min": 150},
  "resting_heart_rate": {"value": 56.0},          // needs password fallback
  "vo2_max":            {"running": 43.0, "running_precise": 42.5}   // needs password fallback
}
```

Resting HR and VO2 Max need an extra `garminconnect` password login because
the garth OAuth scope can't reach those endpoints. Configure
`GARMIN_PASSWORD` (or `password_env_var` in your profile) to enable them;
otherwise the keys are silently absent. Details:
[`docs/garminconnect-fallback.md`](docs/garminconnect-fallback.md).

## CSV export

```bash
garmin-sync export-csv --profile me --start 2026-05-01 --end 2026-05-29 \
    --out ~/garmin-may.csv
```

Flattens the daily JSON files into one row per day with a stable column
schema. Missing values are blank, not `0` — so spreadsheets can tell "no
data" from "value was zero". See [`docs/csv-and-plots.md`](docs/csv-and-plots.md).

## Trend plots

```bash
pip install 'garmin-sync[plots]'

garmin-sync plot --profile me --metric hrv --days 30 --out hrv.png
garmin-sync plot --profile me --metric sleep_score --days 90 --out sleep.png
```

Single-metric line chart + 7-day rolling mean. Headless-safe (Agg backend),
fine to drop into a cron job.

Supported metrics: `hrv`, `hrv_5min_high`, `sleep_score`, `sleep_total_min`,
`steps`, `body_battery_min`, `body_battery_max`, `stress_overall`, `rhr`,
`vo2_max_running`.

## Crontab example

Linux/macOS, sync every morning at 06:30:

```cron
30 6 * * * GARMIN_PASSWORD='...' /usr/local/bin/garmin-sync sync --profile me --days 1 >> /var/log/garmin-sync.log 2>&1
```

## Use as a library

```python
from garmin_sync.auth import authenticate
from garmin_sync.collect import collect_day
from garmin_sync.profile import load_profile
from garmin_sync.storage import write_day_json

profile = load_profile("me")
client = authenticate(profile)
data = collect_day(client, "2026-05-28", profile=profile)
write_day_json(data, profile.output_dir)
```

## FAQ

**Does this work with `garmin.cn` (China region) accounts?**
Yes for sleep, steps, HRV, SpO2, stress, intensity minutes, and activities.
Body Battery, Resting HR, VO2 Max, and Training Readiness return 404 on
`garmin.cn` regardless of token — they're only available on `garmin.com`. If
you have a CN account and want everything, you'll need to migrate (Garmin
support can move accounts).

**Why is `garth` listed as deprecated?**
The upstream `garth` project is in maintenance mode. It still works today.
If/when it stops, garmin-sync will switch to whatever the community
consolidates around. The data fetchers are deliberately thin wrappers so the
auth layer is the only thing that has to change.

**Does it handle MFA?**
Not currently. Disable 2FA during `setup`, then re-enable it. Tokens last
~1 year before the next `setup` is needed.

**Where do my tokens / passwords go?**
Tokens cache as plain JSON in `token_dir` (default `~/.garminconnect-<domain>`).
Passwords are only read from env vars (or `~/.hermes/.env` if present);
nothing is ever written back.

**Will this get rate-limited?**
`garmin-sync sync --days 30` makes roughly 12 API calls × 30 days = ~360
requests. Garmin's per-account limits are generous enough that daily cron
jobs are fine; running it in a loop will eventually 429 you.

## Status

Pre-1.0. The JSON schema is "stable enough that I'm using it daily" but I
may add fields. Removing or renaming an existing field requires a minor
version bump.

## License

[MIT](LICENSE)
