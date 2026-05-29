---
name: garmin-sync
version: 0.1.0
description: "Sync Garmin Connect daily health data (.com / .cn) into local JSON for LLM analysis. Supports multi-profile, garth SSO + garminconnect password fallback for RHR/VO2 Max scopes."
homepage: https://github.com/denkisan/garmin-sync
disable-model-invocation: true
---

# garmin-sync (placeholder)

The English SKILL.md is finalized in batch 5. For now this skill is local-only on the maintainer's machine.

## One-time setup

```bash
pip install garmin-sync
python -m garmin_sync.cli setup --email YOUR_EMAIL --domain garmin.com
```

## Daily sync

```bash
python -m garmin_sync.cli sync --domain garmin.com --days 1
```

JSON files land under `--output-dir` (default `./health/`).
