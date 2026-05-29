"""Garmin Connect authentication via ``garminconnect``.

We use one client per process — :class:`garminconnect.Garmin` with token
persistence via ``login(tokenstore=...)``. Tokens live as a single
``garmin_tokens.json`` file inside ``profile.token_dir`` and auto-refresh
when nearing expiry.
"""
from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

from .profile import Profile

log = logging.getLogger("garmin_sync.auth")


def setup(profile: Profile, email: str, password: str | None = None) -> None:
    """One-time authorization. Persists tokens under ``profile.token_dir``.

    Re-running setup with a valid existing token refreshes it silently.
    Handles MFA interactively via :func:`input`.
    """
    from garminconnect import Garmin

    password = password or load_password_from_env(profile)
    if not password:
        log.error(
            "Need a password. Pass --password or set %s env var.",
            profile.password_env_var,
        )
        sys.exit(1)

    profile.token_dir.mkdir(parents=True, exist_ok=True)
    is_cn = profile.domain == "garmin.cn"

    gc = Garmin(
        email=email,
        password=password,
        is_cn=is_cn,
        prompt_mfa=lambda: input("Garmin MFA code: ").strip(),
    )
    try:
        gc.login(tokenstore=str(profile.token_dir))
        log.info("Authorized. Tokens cached at %s", profile.token_dir)
    except Exception as e:
        log.error("Authorization failed: %s", e)
        sys.exit(1)


def authenticate(profile: Profile):
    """Load cached tokens (and refresh if needed). Returns an authenticated client.

    If tokens are missing or expired beyond auto-refresh, falls back to a fresh
    password login using ``profile.password_env_var``.
    """
    from garminconnect import Garmin

    token_file = profile.token_dir / "garmin_tokens.json"
    if not token_file.exists():
        log.error(
            "No cached tokens at %s. Run `garmin-sync setup` first.",
            profile.token_dir,
        )
        sys.exit(1)

    is_cn = profile.domain == "garmin.cn"
    password = load_password_from_env(profile)  # may be None — only needed on re-login

    gc = Garmin(
        email=profile.email,
        password=password,
        is_cn=is_cn,
        prompt_mfa=lambda: input("Garmin MFA code: ").strip(),
    )
    try:
        gc.login(tokenstore=str(profile.token_dir))
        return gc
    except Exception as e:
        log.error("Auth failed: %s. Tokens may be expired; try `garmin-sync setup` again.", e)
        sys.exit(1)


def load_password_from_env(profile: Profile) -> str | None:
    """Read ``profile.password_env_var`` from env, falling back to ``~/.hermes/.env``."""
    val = os.environ.get(profile.password_env_var)
    if val:
        return val
    env_path = Path.home() / ".hermes" / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            if k.strip() == profile.password_env_var:
                return v.strip()
    return None
