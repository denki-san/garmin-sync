"""Command-line entry point.

Batch 1 supports ``setup`` and ``sync`` subcommands with explicit flags only.
Batch 3 adds ``--profile`` lookup and ``export-csv``; batch 4 adds ``plot``.
"""
from __future__ import annotations

import argparse
import logging
import sys
from datetime import date, timedelta
from pathlib import Path

from .auth import authenticate, setup as setup_cmd
from .collect import collect_day
from .profile import Profile
from .storage import write_day_json


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="garmin-sync", description="Sync Garmin health data to local JSON.")
    p.add_argument("-v", "--verbose", action="store_true", help="Verbose (debug) logging")
    sub = p.add_subparsers(dest="cmd", required=True)

    sp_setup = sub.add_parser("setup", help="One-time SSO authorization")
    sp_setup.add_argument("--email", required=True)
    sp_setup.add_argument("--password", default=None, help="(optional) password; otherwise read from $GARMIN_PASSWORD")
    sp_setup.add_argument("--domain", default="garmin.com", choices=["garmin.com", "garmin.cn"])
    sp_setup.add_argument("--token-dir", default=None, help="Default: ~/.garminconnect-<domain>")

    sp_sync = sub.add_parser("sync", help="Sync N days of health data to JSON")
    g = sp_sync.add_mutually_exclusive_group(required=True)
    g.add_argument("--date", dest="single_date", help="Single date YYYY-MM-DD")
    g.add_argument("--days", type=int, help="Last N days (starting yesterday)")
    sp_sync.add_argument("--domain", default="garmin.com", choices=["garmin.com", "garmin.cn"])
    sp_sync.add_argument("--token-dir", default=None, help="Default: ~/.garminconnect-<domain>")
    sp_sync.add_argument("--output-dir", default="./health", help="Where to write JSON files")
    sp_sync.add_argument("--email", default=None, help="(optional) for garminconnect RHR/VO2 Max fallback")

    return p


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    logging.basicConfig(
        format="[garmin-sync] %(message)s",
        level=logging.DEBUG if args.verbose else logging.INFO,
        stream=sys.stderr,
    )

    if args.cmd == "setup":
        profile = Profile.from_cli(
            domain=args.domain,
            token_dir=args.token_dir,
            output_dir="/tmp",
            email=args.email,
        )
        setup_cmd(profile, args.email, args.password)
        return 0

    if args.cmd == "sync":
        profile = Profile.from_cli(
            domain=args.domain,
            token_dir=args.token_dir,
            output_dir=args.output_dir,
            email=args.email,
        )
        client = authenticate(profile)
        days_to_sync: list[str] = []
        if args.single_date:
            days_to_sync.append(args.single_date)
        else:
            for i in range(1, args.days + 1):
                days_to_sync.append((date.today() - timedelta(days=i)).strftime("%Y-%m-%d"))
        for day in days_to_sync:
            data = collect_day(client, day, profile=profile)
            path = write_day_json(data, Path(profile.output_dir))
            logging.info("wrote %s", path)
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
