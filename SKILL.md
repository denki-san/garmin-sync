---
name: garmin-sync
version: 0.1.0
description: "Sync Garmin Connect daily health data to local JSON for LLM analysis. Supports garmin.com / garmin.cn, multi-profile, CSV export, and matplotlib trend plots. garth SSO for the standard scope + garminconnect password fallback for RHR/VO2 Max."
homepage: https://github.com/denki-san/garmin-sync
disable-model-invocation: true
metadata:
  tags: ["garmin", "health", "fitness", "wearables"]
  requires:
    pips: ["garth", "garminconnect"]
    pips_optional: ["matplotlib"]
    envs_optional: ["GARMIN_PASSWORD"]
---

# garmin-sync

Pulls daily health metrics from Garmin Connect and writes them to disk as
structured JSON, intended to be consumed by an LLM-driven assistant.

See [README.md](README.md) for the full project overview. This file is the
short, agent-facing entry point.

## When to invoke

Use this skill when the user asks about their Garmin data: today's sleep
score, recent HRV trend, stress over the past week, "did I move enough
yesterday", etc. The pattern is:

1. Confirm whether they want today's number or a trend over multiple days.
2. Run `sync` if the relevant date isn't on disk yet.
3. Read the JSON file(s) from `output_dir` and answer.

For trend questions, prefer the JSON files over the CLI — you can do
arbitrary cross-metric analysis (e.g. HRV vs. sleep score correlation) that
the bundled `plot` subcommand can't.

## Commands

```bash
# One-time, per Garmin account
garmin-sync setup --profile me --email you@example.com

# Daily — keep this in cron
garmin-sync sync --profile me --days 1

# Backfill, e.g. when first setting up
garmin-sync sync --profile me --days 60

# Export to CSV for spreadsheet/Grafana
garmin-sync export-csv --profile me --start 2026-05-01 --end 2026-05-31 --out /tmp/may.csv

# Quick trend chart (needs matplotlib)
garmin-sync plot --profile me --metric hrv --days 30 --out /tmp/hrv.png
```

## Data location

By default each profile writes to its configured `output_dir`. One JSON file
per day, named `YYYY-MM-DD.json`. Read directly:

```python
import json, glob
from pathlib import Path

# Last 7 days for the "me" profile (example path)
files = sorted(Path("~/garmin-data/me").expanduser().glob("*.json"))[-7:]
days = [json.loads(p.read_text()) for p in files]
avg_hrv = sum(d["hrv"]["last_night_ms"] for d in days if "hrv" in d) / len(days)
```

## Common requests and where to look

| User asks | Read |
|---|---|
| "How did I sleep last night?" | `sleep.score`, `sleep.stages.deep_min/rem_min`, `sleep.start/end` |
| "HRV trend this week" | `hrv.last_night_ms` across 7 daily files |
| "Was my Body Battery low yesterday?" | `body_battery.min`, `body_battery.drained` |
| "How stressed have I been?" | `stress.overall` + `stress.{rest,low,medium,high}_min` |
| "Resting HR trending up?" | `resting_heart_rate.value` (needs password fallback) |
| "Did I exercise enough this week?" | `intensity_minutes.{moderate,vigorous}_min` + `weekly_goal_min` |

## When data is missing

A key being absent from JSON means the fetcher returned nothing — usually
because the device wasn't worn long enough, the endpoint 404'd for that
domain, or (for RHR/VO2 Max) the password fallback isn't configured.

Run `garmin-sync sync --verbose ...` to see which fetcher failed. See
[docs/auth-troubleshooting.md](docs/auth-troubleshooting.md).
