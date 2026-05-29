# Authentication troubleshooting

`garmin-sync` authenticates via [`garminconnect`](https://github.com/cyberjunky/python-garminconnect),
which uses `curl_cffi` to mimic a real Chrome browser through Garmin's
current SSO flow. There is no separate fallback path — all metrics flow
through the same session.

## The setup flow

```bash
garmin-sync setup --profile me --email you@example.com
# Prompts for password (or set $GARMIN_PASSWORD); prompts for MFA code if needed
```

What happens under the hood:

1. POST your credentials to `sso.<domain>/sso/signin` over a Chrome-impersonated TLS session.
2. If Garmin returns an MFA challenge, prompt for the 6-digit code (`input()`).
3. Exchange the resulting ticket for OAuth1 + OAuth2 tokens via `/oauth-service/oauth/preauthorized`.
4. Write `garmin_tokens.json` (a single file holding both tokens + refresh metadata) into the profile's `token_dir`.

Subsequent `garmin-sync sync` runs load that file. The package transparently
calls `_refresh_session()` when the access token is about to expire, so a
healthy daily-cron setup should not need re-authentication for many months.

## MFA

Interactive prompt by default. To skip the prompt in non-interactive
environments (e.g. cron), pre-generate the token by running `setup`
yourself, then keep the token file alive — cron only needs `sync` after
that, which never re-prompts.

If your account uses an authenticator app (TOTP) you can also feed the code
through a wrapper:

```bash
garmin-sync setup --profile me --email you@example.com < <(echo "$(oathtool --totp -b 'YOUR_TOTP_SECRET')")
```

## Common errors

### `setup` returns 401 or "Invalid credentials"

Double-check the email/password by signing in to Garmin Connect's web UI.
If the password works there but `setup` fails, your account may be in a
captcha-required state — log in once via the website (which clears the
captcha flag) and retry.

### `setup` returns 429

You're being rate-limited by Garmin's IP-level protection. Wait several
minutes between attempts; hammering it extends the cooldown.

### `setup` works but `sync` says "No cached tokens"

The token directory differs between `setup` and `sync`. This usually means
you passed `--token-dir` in one but not the other, or your `profile.token_dir`
doesn't match. Run `garmin-sync sync --verbose --profile NAME` to see the
exact path it's reading from.

### Some metrics missing from JSON

Most often the device wasn't worn long enough to produce that metric for
the day in question. Verify by checking the metric in the Garmin Connect
app for the same day. If the app shows a value but `garmin-sync` doesn't,
file an issue with the verbose log.

### `body_battery`, `training_readiness`, `vo2_max` always missing

Those endpoints **return 404 on `garmin.cn`** regardless of token — they
only exist on `garmin.com`. If you have a `garmin.cn` account and want
them, you'll need to migrate the account to the international region
(Garmin support can do this).

## Re-authorizing

When you change your Garmin Connect password or the token file gets
corrupted:

```bash
garmin-sync setup --profile me --email you@example.com
# overwrites garmin_tokens.json with a fresh one
```

Existing JSON data files in `output_dir` are untouched.

## Token isolation between domains

`garmin.com` and `garmin.cn` tokens **cannot be swapped**. Always use a
distinct `token_dir` per profile/domain.

## Endpoint reference

See [`api-endpoints.md`](api-endpoints.md) for the per-fetcher API paths and
their domain availability.
