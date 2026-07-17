# Configuration system

`browser/pom/base/config.py` is the single source of truth for every credential and every
environment-dependent value this framework uses — every test, fixture, and `browser/checks/`
script goes through it (`load_app_config()`). It replaced the old `driver.py`
`load_config()`/`CONFIG_PATH`/`CONFIG_PATH_FSB`/`load_share_credentials()` functions, which
returned plain, unvalidated dicts.

## Why "5 environments" doesn't mean 5 appliances

This is a QA automation framework testing fixed lab hardware — nbr-84 (FLB) and nbr-5 (FSB), see
`test-data/environment.md` — not a deployed app with Local/Dev/QA/Staging/Production tiers. There
is no dev NBR appliance, no QA NBR appliance, no staging or production one. Only **`local`** is
populated with real data today (the values in your `.env`).

The other 4 names (`dev`, `qa`, `staging`, `production`) are real, working extension points, not
decoration: the system is fully able to switch to one and load an isolated set of secrets for it
the moment a real appliance exists for that tier — it just refuses to pretend one exists today.
Selecting an unprovisioned environment is a hard `ConfigError`, never a silent fallback to
`local`'s values and never a fabricated fake URL.

## Environment switching

Set `NBR_ENV` (case-insensitive) to one of `local` (default) / `dev` / `qa` / `staging` /
`production`:

```bash
pytest tests/e2e -v                    # local (default) — today's real lab appliances
NBR_ENV=qa pytest tests/e2e -v         # requires .env.qa to exist (see below) — else ConfigError
```

An unknown value (`NBR_ENV=prod`, say — not `production`) raises `ConfigError` naming every valid
option.

## Secrets isolation — `.env` layering

Precedence, highest to lowest — every layer is **non-destructive**: a real, already-exported
process/CI env var always wins over anything a file sets.

1. **Real process env vars** (shell `export`, GitHub Actions secrets injected directly) — never
   overridden by a file.
2. **`.env.<environment>`** — only consulted for a non-`local` environment. This is the secrets
   *isolation* mechanism: dev/qa/staging/production each get their own gitignored file, so a
   qa-environment run never reads production's file or vice versa. **If `NBR_ENV` selects one of
   these and its file doesn't exist, `load_app_config()` raises `ConfigError`** naming the exact
   missing path.
3. **Base `.env`** (existing convention, unchanged) — today's real lab-appliance values; loaded
   for every environment, including `local`.
4. **Gitignored JSON fallback** (`browser/config/ui_config*.json`) — kept for anyone whose local
   setup predates `.env`; lowest priority, unchanged behavior from before this system existed.

Layering mechanics: the overlay loads *before* the base file, both with `override=False`
(python-dotenv's "don't clobber a key already in `os.environ`"). That lets the overlay win over
the base file for any key it sets, while a real shell/CI var — present before either file loads —
still wins over both.

### Adding a real dev/qa/staging/production appliance later

1. Create `.env.<environment>` at the repo root (gitignored, same convention as `.env`).
2. Put only the keys that differ for that environment — anything you omit falls back to the base
   `.env`. A fully independent environment can also just repeat every key.
3. Run with `NBR_ENV=<environment> pytest ...` (or the equivalent for a `browser/checks/*.py`
   script — they all resolve through the same `load_app_config()`).

## Typed config object

```python
from browser.pom.base.config import load_app_config

cfg = load_app_config()          # AppConfig — resolves NBR_ENV internally
cfg.environment                  # Environment.LOCAL
cfg.flb.url / .user / .password  # nbr-84 (FLB) — ApplianceCredentials
cfg.fsb.url / .user / .password  # nbr-5 (FSB) — ApplianceCredentials
cfg.share("winfs3").user / .password  # any CIFS/NFS export-target host — ShareCredentials
```

`ApplianceCredentials`/`ShareCredentials`/`AppConfig` are frozen `dataclasses` — no dict-key
typos, IDE-autocompletable fields, immutable once resolved.

## Validation

Nothing is validated automatically at load time — `load_app_config()` always succeeds and returns
whatever it found, including `None` fields, so code that doesn't need a guarantee (e.g. the
`nbr_config_fsb` fixture, unused by any suite today) isn't forced to fail just because FSB isn't
configured. Call `.validate(label)` explicitly wherever a real, complete credential set is
actually required:

```python
cfg.flb.validate("NBR_FLB")   # raises ConfigError listing EVERY missing/malformed field at once
```

Every `browser/checks/*.py` script that logs into the Director UI, and `conftest.py`'s
`nbr_config` fixture (since virtually every test depends on a working FLB login), call this
before use — replacing several scripts' previous ad-hoc `if not cfg.get("url") or ...` checks, and
adding the same fail-fast clarity to every script that had no check at all. A missing credential
now surfaces as `Invalid NBR_FLB configuration: NBR_FLB_URL is not set; NBR_FLB_PASS is not set`
instead of an obscure downstream Playwright/login crash.

## Testing this module

`tests/e2e/test_infrastructure/test_config.py` — pure-logic unit tests (no browser, no
appliance), isolated from the real `.env`/JSON files via a `tmp_path`-redirected `_REPO_ROOT`.
Covers: default/explicit environment selection, the unknown-value and
unprovisioned-environment error paths, `.env.<environment>` overlay precedence, real-env-var
precedence, and every validation rule.
