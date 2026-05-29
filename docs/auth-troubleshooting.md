# Authentication troubleshooting

`garmin-sync` uses [`garth`](https://github.com/matin/garth) for the primary
SSO flow and [`garminconnect`](https://github.com/cyberjunky/python-garminconnect)
as a password-login fallback for a few advanced endpoints.

> **Heads-up**: as of 2026, `garth` is in maintenance mode (see the deprecation
> notice on the [garth repo](https://github.com/matin/garth/discussions/222)).
> It still works against current Garmin Connect APIs, but the underlying
> authentication endpoints are subject to change without notice. If `setup`
> starts failing after a successful one-time auth, that's the first thing to
> check.

## The setup flow

```bash
garmin-sync setup --domain garmin.com --email you@example.com
# enters interactive password prompt if --password not given
```

What happens under the hood:

1. GET `https://sso.<domain>/sso/embed` to grab the initial cookie.
2. GET `https://sso.<domain>/sso/signin` to get a CSRF token.
3. POST the username/password/CSRF as a form (`embed=true`).
4. Parse the response HTML to extract `ticket=...`.
5. Use the ticket against `/oauth-service/oauth/preauthorized` on `connectapi.<domain>` to exchange for OAuth1, then OAuth2 tokens.
6. Write `oauth1_token.json` + `oauth2_token.json` into the profile's `token_dir`.

Tokens are valid roughly **1 year**, after which `setup` needs to run again.

## Common errors

### `setup` returns 429 immediately

You're being rate-limited by Garmin's IP-level protection. Wait at least a few
minutes between attempts. Hammering it can extend the cooldown.

### `setup` returns 401 / "Account has 2FA enabled"

`garth`'s SSO flow does not support MFA prompts. Disable 2FA temporarily in
the Garmin Connect mobile app, run `setup`, then re-enable it. Cached tokens
keep working for ~1 year after that.

### `setup` works but `sync` returns "No cached tokens"

The token directory differs between `setup` and `sync`. This usually means
you passed `--token-dir` in one but not the other, or your `profile.token_dir`
doesn't match. Run `garmin-sync sync --profile NAME` and watch the logged path.

### Some metrics are missing (`spo2`, `body_battery`, `respiration`)

These come from per-day `connectapi` endpoints that quietly return empty for
days when the device wasn't worn long enough. Check a known-good day. If
*every* day is empty, your account region may not be served by those endpoints
(see "Domain caveat" in [`api-endpoints.md`](api-endpoints.md)).

### `resting_heart_rate` / `vo2_max` always absent

These need the garminconnect fallback. Make sure:

1. `garminconnect` is installed (`pip install garminconnect`, or via `garmin-sync[plots]` doesn't include it — install separately if needed).
2. Your profile has an `email` field (or `GARMIN_EMAIL` is set).
3. The env var named by `password_env_var` (default `GARMIN_PASSWORD`) contains the account password, or `~/.hermes/.env` has a `GARMIN_PASSWORD=...` line.
4. Run with `--verbose` to see why the fallback short-circuits.

## Why password login for RHR / VO2 Max?

Garmin's API gates endpoints by OAuth scope. The web-embed SSO scope that
`garth` requests doesn't cover `/userstats-service/*` or
`/metrics-service/metrics/maxmet/*` — both return `403`. `garminconnect`
re-logs in with password, which (currently) yields a token with a wider scope
that includes those paths.

This is a known upstream quirk, not something garmin-sync invented; see the
[garminconnect issue tracker](https://github.com/cyberjunky/python-garminconnect/issues)
for context.

## Re-authorizing

When tokens expire (~1 year) or rotate after a Garmin Connect password change:

```bash
# Just re-run setup; it overwrites the existing token files.
garmin-sync setup --profile me
```

Existing JSON data files in `output_dir` are untouched.

## Token isolation between domains

`garmin.com` and `garmin.cn` tokens **cannot be swapped**. The garth Client
binds its requests to the domain it was constructed with, but if you load a
`.cn`-issued token into a Client constructed for `.com`, the loaded tokens
override the domain and you end up calling the wrong host.

Always use a distinct `token_dir` per domain. Profiles handle this for you
when each profile names its own `token_dir`.
