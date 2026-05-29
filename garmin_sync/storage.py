"""Filesystem layout: ``<output_dir>/<YYYY-MM-DD>.json``."""
from __future__ import annotations

import json
from pathlib import Path


def write_day_json(data: dict, output_dir: Path) -> Path:
    output_dir = Path(output_dir).expanduser()
    output_dir.mkdir(parents=True, exist_ok=True)
    day = data["date"]
    path = output_dir / f"{day}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return path


def read_day_json(output_dir: Path, day: str) -> dict | None:
    path = Path(output_dir).expanduser() / f"{day}.json"
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def list_days(output_dir: Path) -> list[str]:
    output_dir = Path(output_dir).expanduser()
    if not output_dir.exists():
        return []
    return sorted(p.stem for p in output_dir.glob("*.json"))
