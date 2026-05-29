"""Profile abstraction for multi-user support.

Batch 1 only defines the dataclass and a fallback derived from CLI flags.
Batch 3 adds ``~/.config/garmin-sync/profiles.toml`` loading.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Profile:
    name: str
    domain: str
    token_dir: Path
    output_dir: Path
    email: str | None = None
    password_env_var: str = "GARMIN_PASSWORD"

    @classmethod
    def from_cli(
        cls,
        *,
        domain: str,
        token_dir: str | Path | None,
        output_dir: str | Path,
        name: str = "default",
        email: str | None = None,
        password_env_var: str = "GARMIN_PASSWORD",
    ) -> "Profile":
        if token_dir is None:
            token_dir = Path.home() / f".garminconnect-{domain.replace('.', '_')}"
        return cls(
            name=name,
            domain=domain,
            token_dir=Path(token_dir).expanduser(),
            output_dir=Path(output_dir).expanduser(),
            email=email,
            password_env_var=password_env_var,
        )
