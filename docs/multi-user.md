# Multi-user profiles

`garmin-sync` supports multiple Garmin accounts on the same machine via named
profiles stored in `~/.config/garmin-sync/profiles.toml`.

## File location

```
~/.config/garmin-sync/profiles.toml
```

(Follows the XDG Base Directory spec. Create the directory if it doesn't exist.)

## Format

```toml
[profiles.me]
email            = "you@example.com"
domain           = "garmin.com"
token_dir        = "~/.garminconnect-garmin_com"
output_dir       = "~/garmin-data/me"
password_env_var = "GARMIN_PASSWORD"   # optional, default is GARMIN_PASSWORD

[profiles.spouse]
email            = "spouse@example.com"
domain           = "garmin.cn"
token_dir        = "~/.garminconnect-spouse-cn"
output_dir       = "~/garmin-data/spouse"
password_env_var = "SPOUSE_GARMIN_PASSWORD"   # separate env var per profile
```

### Fields

| Field | Required | Notes |
|---|---|---|
| `email` | recommended | Needed for the garminconnect password fallback (RHR, VO2 Max). |
| `domain` | yes | `garmin.com` for international, `garmin.cn` for China. |
| `token_dir` | no | Defaults to `~/.garminconnect-<domain_with_underscore>`. |
| `output_dir` | yes | Where daily JSON files are written. |
| `password_env_var` | no | Defaults to `GARMIN_PASSWORD`. Use a different one per profile if you have multiple accounts. |

## Usage

```bash
# One-time auth per profile
garmin-sync setup --profile me --email you@example.com
garmin-sync setup --profile spouse --email spouse@example.com

# Daily sync
garmin-sync sync --profile me --days 1
garmin-sync sync --profile spouse --days 1
```

CLI flags override the profile fields, so you can do:

```bash
garmin-sync sync --profile me --output-dir /tmp/test --days 1
```

## Token isolation

Each profile writes its `oauth1_token.json` / `oauth2_token.json` into its own
`token_dir`. Never share one token dir between two domains — the auth layer
will silently overwrite the other domain's tokens.

## Per-profile passwords

`garmin-sync` only needs the password when running `setup` (or when cached
tokens have fully expired and need a fresh login). For multiple accounts on
one machine, give each profile a distinct `password_env_var` so they don't
share a single `GARMIN_PASSWORD`:

```bash
export SPOUSE_GARMIN_PASSWORD='...'
garmin-sync setup --profile spouse --email spouse@example.com
```

You can also put them in `~/.hermes/.env` (`KEY=value` per line); the auth
loader reads them from there if they aren't in the environment.
