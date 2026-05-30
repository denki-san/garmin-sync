# Authentication troubleshooting

`garmin-sync` authenticates via [`garminconnect`](https://github.com/cyberjunky/python-garminconnect),
which uses `curl_cffi` to mimic a real Chrome browser through Garmin's
current SSO flow. There is no separate fallback path — all metrics flow
through the same session. Basic `setup` / MFA usage is covered in the README;
this page only lists what to do when something breaks.

## `setup` returns 401 or "Invalid credentials"

Double-check the email/password by signing in to Garmin Connect's web UI.
If the password works there but `setup` fails, your account may be in a
captcha-required state — log in once via the website (which clears the
captcha flag) and retry.

## `setup` returns 429

You're being rate-limited by Garmin's IP-level protection. Wait several
minutes between attempts; hammering it extends the cooldown.

## `setup` works but `sync` says "No cached tokens"

The token directory differs between `setup` and `sync`. This usually means
you passed `--token-dir` in one but not the other, or your `profile.token_dir`
doesn't match. Run `garmin-sync sync --verbose --profile NAME` to see the
exact path it's reading from.

## Some metrics missing from JSON

Most often the device wasn't worn long enough to produce that metric for
the day in question. Verify by checking the metric in the Garmin Connect
app for the same day. If the app shows a value but `garmin-sync` doesn't,
file an issue with the verbose log.

## `body_battery`, `training_readiness`, `vo2_max` always missing

Those endpoints **return 404 on `garmin.cn`** regardless of token — they
only exist on `garmin.com`. If you have a `garmin.cn` account and want
them, you'll need to migrate the account to the international region
(Garmin support can do this).
