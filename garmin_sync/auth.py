"""Garmin Connect authentication.

Primary: garth web-embed SSO. Token cached to ``profile.token_dir``.
Fallback for RHR / VO2 Max scopes: garminconnect password login (requires
``GARMIN_PASSWORD`` env var).
"""
from __future__ import annotations

import logging
import os
import sys
import time
from pathlib import Path

from .profile import Profile

log = logging.getLogger("garmin_sync.auth")


def setup(profile: Profile, email: str, password: str | None = None) -> None:
    """One-time SSO authorization. Writes OAuth1/OAuth2 tokens to ``profile.token_dir``."""
    import garth

    password = os.environ.get(profile.password_env_var) or password
    if not password:
        log.error(
            "Need a password. Pass --password or set %s env var.",
            profile.password_env_var,
        )
        sys.exit(1)

    profile.token_dir.mkdir(parents=True, exist_ok=True)

    for attempt in range(3):
        try:
            client = garth.Client(domain=profile.domain)
            client.login(email, password)
            client.dump(str(profile.token_dir))
            log.info("Authorized. Tokens cached at %s", profile.token_dir)
            log.info("Tokens are valid ~1 year; re-run setup when they expire.")
            return
        except Exception as e:
            err_str = str(e).lower()
            if "mfa" in err_str or "two-factor" in err_str:
                log.error(
                    "Account has 2FA enabled. Disable it in Garmin Connect app first."
                )
                sys.exit(1)
            wait = 2**attempt
            log.warning("Auth attempt %d failed (%s); retry in %ds", attempt + 1, e, wait)
            time.sleep(wait)

    log.error("Authorization failed after retries.")
    sys.exit(1)


def authenticate(profile: Profile):
    """Load cached garth tokens and return an authenticated client."""
    import garth

    oauth1 = profile.token_dir / "oauth1_token.json"
    oauth2 = profile.token_dir / "oauth2_token.json"
    if not profile.token_dir.exists() or not oauth1.exists() or not oauth2.exists():
        log.error("No cached tokens at %s. Run `garmin-sync setup` first.", profile.token_dir)
        sys.exit(1)

    for attempt in range(3):
        try:
            client = garth.Client(domain=profile.domain)
            client.load(str(profile.token_dir))
            _ = client.username  # probe
            return client
        except Exception as e:
            if attempt < 2:
                wait = 2**attempt
                log.warning("Auth attempt %d failed (%s); retry in %ds", attempt + 1, e, wait)
                time.sleep(wait)
            else:
                log.error("Auth failed: %s. Tokens may be expired; re-run setup.", e)
                sys.exit(1)


def load_password_from_env(profile: Profile) -> str | None:
    """Look up the password env var, falling back to ``~/.hermes/.env`` if present."""
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


_gc_client_cache: dict[str, object] = {}


def get_garminconnect_client(profile: Profile):
    """Lazy garminconnect password-login client, cached per (email, domain).

    Returns ``None`` when no password is available — callers should treat advanced
    fetchers (RHR, VO2 Max) as best-effort.
    """
    cache_key = f"{profile.email or os.environ.get('GARMIN_EMAIL', '')}:{profile.domain}"
    if cache_key in _gc_client_cache:
        cached = _gc_client_cache[cache_key]
        return cached if cached is not False else None

    try:
        from garminconnect import Garmin
    except ImportError:
        log.debug("garminconnect not installed; advanced endpoints disabled.")
        _gc_client_cache[cache_key] = False
        return None

    email = profile.email or os.environ.get("GARMIN_EMAIL")
    password = load_password_from_env(profile)
    if not email or not password:
        _gc_client_cache[cache_key] = False
        return None

    try:
        is_cn = profile.domain == "garmin.cn"
        gc = Garmin(email=email, password=password, is_cn=is_cn)
        gc.login()
        _gc_client_cache[cache_key] = gc
        return gc
    except Exception as e:
        log.debug("garminconnect login failed: %s", e)
        _gc_client_cache[cache_key] = False
        return None
