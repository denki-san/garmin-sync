# garmin-sync

> Sync Garmin Connect health data to local JSON. Designed for LLM-driven analysis (Claude Code, Codex, Hermes, etc.).

Full README is coming together in batch 5 — this file is a placeholder.

## Status

- [x] Batch 1: Skeleton + core fetchers + JSON output
- [ ] Batch 2: Personal fork (`garmin-cn`) plugin-ization
- [ ] Batch 3: Multi-profile TOML config + CSV export
- [ ] Batch 4: matplotlib trend plots
- [ ] Batch 5: English docs + publish prep

## Quick smoke test

```bash
python -m garmin_sync.cli sync \
    --domain garmin.com \
    --token-dir ~/.garminconnect-garmin_com \
    --output-dir /tmp/garmin-sync-out \
    --days 1
```
