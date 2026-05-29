"""Profile abstraction for multi-user support.

Profiles can be defined three ways (later wins):

1. Built-in defaults derived from CLI flags via ``Profile.from_cli``.
2. ``~/.config/garmin-sync/profiles.toml`` (XDG standard).
3. Per-invocation overrides on the ``garmin-sync ... --token-dir / --output-dir`` flags.

The TOML format::

    [profiles.lei]
    email       = "you@example.com"
    domain      = "garmin.com"
    token_dir   = "~/.garminconnect-garmin_com"
    output_dir  = "~/.hermes/skills/garmin-cn/health"
    password_env_var = "GARMIN_PASSWORD"   # optional, default GARMIN_PASSWORD

    [profiles.wife]
    email       = "her@example.com"
    domain      = "garmin.cn"
    token_dir   = "~/.garminconnect-wife-cn"
    output_dir  = "~/garmin-data/wife"
    password_env_var = "WIFE_GARMIN_PASSWORD"
"""
from __future__ import annotations

import logging
import sys
from dataclasses import dataclass, replace
from pathlib import Path

log = logging.getLogger("garmin_sync.profile")

DEFAULT_CONFIG_PATH = Path.home() / ".config" / "garmin-sync" / "profiles.toml"


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


def _load_toml(path: Path) -> dict:
    if sys.version_info >= (3, 11):
        import tomllib
        with open(path, "rb") as f:
            return tomllib.load(f)
    import tomli
    with open(path, "rb") as f:
        return tomli.load(f)


def load_profile(name: str, config_path: Path | None = None) -> Profile:
    """Load a named profile from ``profiles.toml``. Raises SystemExit if missing."""
    path = config_path or DEFAULT_CONFIG_PATH
    if not path.exists():
        log.error(
            "Profile '%s' requested but %s does not exist. Create it (see docs/multi-user.md).",
            name, path,
        )
        sys.exit(2)
    data = _load_toml(path)
    profiles = data.get("profiles", {})
    if name not in profiles:
        log.error("Profile '%s' not found in %s. Available: %s",
                  name, path, ", ".join(sorted(profiles.keys())) or "(none)")
        sys.exit(2)
    entry = profiles[name]

    domain = entry.get("domain", "garmin.com")
    if domain not in ("garmin.com", "garmin.cn"):
        log.error("Invalid domain %r in profile %s", domain, name)
        sys.exit(2)

    token_dir = entry.get("token_dir")
    if token_dir is None:
        token_dir = Path.home() / f".garminconnect-{domain.replace('.', '_')}"

    output_dir = entry.get("output_dir")
    if output_dir is None:
        log.error("Profile %s missing required field: output_dir", name)
        sys.exit(2)

    return Profile(
        name=name,
        domain=domain,
        token_dir=Path(token_dir).expanduser(),
        output_dir=Path(output_dir).expanduser(),
        email=entry.get("email"),
        password_env_var=entry.get("password_env_var", "GARMIN_PASSWORD"),
    )


def resolve_profile(
    *,
    profile_name: str | None,
    domain: str | None,
    token_dir: str | Path | None,
    output_dir: str | Path | None,
    email: str | None = None,
    config_path: Path | None = None,
) -> Profile:
    """Combine TOML profile (if named) with CLI overrides.

    - If ``profile_name`` is given, start from TOML and override per-field.
    - Otherwise build from CLI flags (domain/token_dir/output_dir all required for sync).
    """
    if profile_name:
        base = load_profile(profile_name, config_path=config_path)
        overrides: dict = {}
        if domain is not None and domain != base.domain:
            overrides["domain"] = domain
        if token_dir is not None:
            overrides["token_dir"] = Path(token_dir).expanduser()
        if output_dir is not None:
            overrides["output_dir"] = Path(output_dir).expanduser()
        if email is not None:
            overrides["email"] = email
        return replace(base, **overrides) if overrides else base

    if domain is None:
        domain = "garmin.com"
    if output_dir is None:
        log.error("Either --profile or --output-dir is required for this command.")
        sys.exit(2)
    return Profile.from_cli(
        domain=domain,
        token_dir=token_dir,
        output_dir=output_dir,
        email=email,
    )
