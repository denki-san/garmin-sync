"""Command-line entry point.

Subcommands:
    setup       — one-time SSO authorization
    sync        — fetch N days of health data to JSON
    export-csv  — flatten previously-synced JSON files into one CSV

Profiles: pass ``--profile NAME`` to load defaults from
``~/.config/garmin-sync/profiles.toml``. Individual flags still override.
"""
from __future__ import annotations

import argparse
import logging
import sys
from datetime import date, timedelta
from pathlib import Path

from .auth import authenticate, setup as setup_cmd
from .collect import collect_day
from .export.csv import export_csv
from .profile import Profile, resolve_profile
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
    sp_setup.add_argument("--profile", default=None, help="Use defaults from profiles.toml")

    sp_sync = sub.add_parser("sync", help="Sync N days of health data to JSON")
    g = sp_sync.add_mutually_exclusive_group(required=True)
    g.add_argument("--date", dest="single_date", help="Single date YYYY-MM-DD")
    g.add_argument("--days", type=int, help="Last N days (starting yesterday)")
    sp_sync.add_argument("--profile", default=None, help="Use defaults from profiles.toml")
    sp_sync.add_argument("--domain", default=None, choices=["garmin.com", "garmin.cn"])
    sp_sync.add_argument("--token-dir", default=None, help="Override profile's token_dir")
    sp_sync.add_argument("--output-dir", default=None, help="Override profile's output_dir")
    sp_sync.add_argument("--email", default=None, help="(optional) for garminconnect RHR/VO2 Max fallback")

    sp_csv = sub.add_parser("export-csv", help="Flatten synced JSON files into a CSV")
    sp_csv.add_argument("--profile", default=None, help="Use defaults from profiles.toml")
    sp_csv.add_argument("--input-dir", default=None, help="Override profile's output_dir as CSV source")
    sp_csv.add_argument("--start", required=True, help="Inclusive start date YYYY-MM-DD")
    sp_csv.add_argument("--end", required=True, help="Inclusive end date YYYY-MM-DD")
    sp_csv.add_argument("--out", required=True, help="Output CSV file path")

    sp_plot = sub.add_parser("plot", help="Plot a metric trend as a PNG (requires [plots] extra)")
    sp_plot.add_argument("--profile", default=None, help="Use defaults from profiles.toml")
    sp_plot.add_argument("--input-dir", default=None, help="Override profile's output_dir")
    sp_plot.add_argument("--metric", required=True, help="Metric key (use --list-metrics to see options)")
    sp_plot.add_argument("--days", type=int, default=30, help="Number of days to plot (default 30)")
    sp_plot.add_argument("--end-date", default=None, help="Last day on x-axis YYYY-MM-DD (default: yesterday)")
    sp_plot.add_argument("--out", required=True, help="Output PNG file path")
    sp_plot.add_argument("--rolling", type=int, default=7, help="Rolling-mean window in days (default 7)")
    sp_plot.add_argument("--title", default=None, help="Optional custom title")
    sp_plot.add_argument("--list-metrics", action="store_true", help="Print supported metrics and exit")

    return p


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    logging.basicConfig(
        format="[garmin-sync] %(message)s",
        level=logging.DEBUG if args.verbose else logging.INFO,
        stream=sys.stderr,
    )

    if args.cmd == "setup":
        if args.profile:
            profile = resolve_profile(
                profile_name=args.profile,
                domain=args.domain,
                token_dir=args.token_dir,
                output_dir="/tmp",
                email=args.email,
            )
        else:
            profile = Profile.from_cli(
                domain=args.domain or "garmin.com",
                token_dir=args.token_dir,
                output_dir="/tmp",
                email=args.email,
            )
        setup_cmd(profile, args.email, args.password)
        return 0

    if args.cmd == "sync":
        profile = resolve_profile(
            profile_name=args.profile,
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
            data = collect_day(client, day)
            path = write_day_json(data, Path(profile.output_dir))
            logging.info("wrote %s", path)
        return 0

    if args.cmd == "export-csv":
        if args.input_dir:
            input_dir = Path(args.input_dir).expanduser()
        else:
            if not args.profile:
                logging.error("export-csv: need --profile or --input-dir")
                return 2
            profile = resolve_profile(
                profile_name=args.profile,
                domain=None,
                token_dir=None,
                output_dir=None,
                email=None,
            )
            input_dir = profile.output_dir
        n = export_csv(input_dir, args.start, args.end, Path(args.out))
        logging.info("wrote %s (%d rows, from %s)", args.out, n, input_dir)
        return 0

    if args.cmd == "plot":
        try:
            from .export.plots import plot_metric, list_metrics
        except ImportError:
            logging.error("plot requires matplotlib. Install: pip install garmin-sync[plots]")
            return 2

        if args.list_metrics:
            print("Supported metrics:")
            for m in list_metrics():
                print(f"  {m}")
            return 0

        if args.input_dir:
            input_dir = Path(args.input_dir).expanduser()
        else:
            if not args.profile:
                logging.error("plot: need --profile or --input-dir")
                return 2
            profile = resolve_profile(
                profile_name=args.profile,
                domain=None,
                token_dir=None,
                output_dir=None,
                email=None,
            )
            input_dir = profile.output_dir

        out = plot_metric(
            input_dir=input_dir,
            metric=args.metric,
            days=args.days,
            out_path=Path(args.out),
            end_date=args.end_date,
            rolling_window=args.rolling,
            title=args.title,
        )
        logging.info("wrote %s", out)
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
