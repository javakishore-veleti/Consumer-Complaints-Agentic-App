# M01-0073 — containers stop always removes Docker volumes

**Issue:** #133 · **Feature:** #2 · **Epic:** #1

## Decision

Local `docker compose down` for CCA always removes named volumes by default (`-v`). Local restarts should not reuse stale Airflow metadata, Mongo data, or operational Postgres data unless the operator opts in.

## Behavior

| Invocation | Volumes |
|---|---|
| `npm run local:containers:all:stop` / profile `:stop` / `docker-all-down.sh` | **Removed** (`docker compose down -v`) |
| Same with `--keep-volumes` | Kept (`docker compose down` only) |
| Same with `--wipe` | Removed (no-op alias; default already wipes) |

Applies to every service resolved by the existing profile / all / explicit-name logic (`docker-profiles.sh`).

## Out of scope

- `local:portals:all:stop`, Middleware `run_app.sh stop`
- Changing what volumes compose files declare

## Files

- `CICD/Local/docker-profiles.sh` — parse `--keep-volumes`; default wipe on
- `CICD/Local/docker-all-down.sh` — always `-v` unless keep
- Root `README.md` — document wipe-on-stop

## Verification

- Script comments and `--help`/header text match behavior
- Manual: after `up`, `stop` without keep → `docker volume ls` no longer shows that project's volumes (or compose reports removing them)
