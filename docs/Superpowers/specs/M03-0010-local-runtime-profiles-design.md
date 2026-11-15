# M03-0010 (#120) npm/docker profiles: SQLite-lite default; Postgres and Mongo opt-in

Decisions: **D78** in `Middleware/ConsumerComplaintsHandsOn/DESIGN.md` (builds on D75–D77). Decided without the user present (unattended story #120); review and reverse if needed.

## Goal

Local developers start only the containers each operational-store profile needs. Default (SQLite-lite) is Airflow only — no operational Postgres container and no Mongo. Postgres and Mongo containers are opt-in. Document the sets; keep `local:containers:all:*` unchanged.

## Approaches considered

| | Approach | Trade-off |
|---|---|---|
| A (chosen) | Shared `profiles.map` + `docker-profiles.sh`; `--profile` on existing `docker-all-*.sh`; named npm scripts per profile; add `CICD/Local/postgres` compose | Minimal surface; all:* stays discover-everything; status shows expected set |
| B | Separate up/down scripts per profile, leave `docker-all-*` alone | Duplicates compose invocation logic |
| C | Change no-args `docker-all-up` default to sqlite-only | Breaks existing “start everything” expectation |

## D78 — Lite local container profiles

1. **Profiles → containers** (operational store; API and Admin UI stay host npm processes):
   - `sqlite` (default): `airflow` only. Airflow’s *internal* Postgres for Airflow metadata is part of that compose and is not the CCA operational store.
   - `postgres`: `airflow` + `postgres` (new `CICD/Local/postgres` — operational CCA DB, D77).
   - `mongodb`: `airflow` + `mongodb`.
2. **`local:containers:all:*` unchanged:** no args still starts/stops/status every `CICD/Local/*/docker-compose.y*ml`.
3. **Profile entry points:** `docker-all-{up,down,status}.sh --profile <name>` and npm scripts `local:containers:{sqlite,postgres,mongodb}:{start,stop,status}`.
4. **Status** with `--profile` prints the profile name, the expected service list, then `docker compose ps` for those services only.
5. **Docs:** README + ARCHITECTURE §8 list container sets; `.env.example` Profile 2 points at `npm run local:containers:postgres:start` (keep `docker run` as alternate).

## Out of scope

- Mongo DAO impl (#119), Admin UI (#121/#122), DoD matrix (#123), changing Airflow’s internal Postgres.

## Self-review

- No placeholders; `all:*` explicitly preserved.
- Operational Postgres compose is separate from Airflow’s `postgres` service (different compose project / container name).
