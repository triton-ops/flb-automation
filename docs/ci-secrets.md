# CI secrets for the `e2e-appliance` job

`.github/workflows/ci.yml`'s `e2e-appliance` job needs the same credentials this project already
loads locally from `.env` (see `.env.example` and `browser/pom/base/config.py`'s `load_app_config()`
— docs/configuration.md).
In CI these come from GitHub repository secrets instead of a checked-out `.env` file, since `.env`
is gitignored and must never be committed.

**Status: unverified.** This mapping is best-effort, written from the existing `.env.example`
fixture list — no self-hosted runner is provisioned for this repo yet (see the `e2e-appliance`
job's own `runs-on: [self-hosted, flb-lab]` and its comment), so this workflow path has not
actually been exercised end-to-end.

## Setting the secrets

Repo → Settings → Secrets and variables → Actions → New repository secret. Add one secret per row
below, matching `.env.example`'s values exactly:

| Secret name | Source |
|---|---|
| `NBR_FLB_URL` | `test-data/environment.md` — nbr-84 appliance URL |
| `NBR_FLB_USER` | nbr-84 login |
| `NBR_FLB_PASS` | nbr-84 password |
| `NBR_FSB_URL` | `test-data/environment.md` — nbr-5 appliance URL |
| `NBR_FSB_USER` | nbr-5 login |
| `NBR_FSB_PASS` | nbr-5 password |
| `WINFS3_USER` | win-fs3 CIFS/NFS export target login |
| `WINFS3_PASS` | win-fs3 password |

The workflow writes these into a `.env` file at job start (see the "Write .env from repository
secrets" step) so `load_app_config()` picks them up exactly as it would locally — no code path
differs between local and CI runs. (This also means the CI runner's environment is implicitly
`NBR_ENV=local` — the same "today's only real target" environment used everywhere else.)

## Runner requirement

The appliance URLs are private RFC1918 addresses (10.10.16.84, 10.10.15.5) with no route from a
GitHub-hosted runner. The `e2e-appliance` job is pinned to `runs-on: [self-hosted, flb-lab]` — a
self-hosted runner registered on the same network as the appliances, labeled `flb-lab`. Until that
runner exists, `workflow_dispatch`'s `run_e2e` input has no effect (the job has nowhere to run).

## Why this job doesn't run on every push

Per `CLAUDE.md`'s safety fence and the "no concurrent jobs against the same source" constraint —
this suite drives real jobs against shared lab appliances one suite at a time. Running it on every
push/PR would risk overlapping runs against the same source VID. It's `workflow_dispatch`-gated
(manual, opt-in via the `run_e2e` input) instead.
