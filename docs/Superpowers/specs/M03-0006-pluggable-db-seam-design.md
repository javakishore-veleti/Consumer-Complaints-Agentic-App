# M03-0006 (#116) Pluggable local operational DB seam (SQLite / Postgres / MongoDB)

Decisions: **D75** in `Middleware/ConsumerComplaintsHandsOn/DESIGN.md` (also D9, D23, D33, D45, D48, D51, D64). Decided without the user present (unattended story #116); review and reverse if needed.

## Goal

Lock the **seam** so the same admin/operational store (workflows, MIOs, catalog, ingest/exec logs) can run on **SQLite** (default, fewest containers), **Postgres** (via `CCA_DB_URL`), or **MongoDB** (via `.env`), without rewriting facades, services, or API. Callers stay on DAO interfaces; `DaoObjectsFactory.init()` (D45) chooses the implementation. Full Mongo DAO impls are **out of scope** here (story #119).

## Approaches considered

| | Approach | Trade-off |
|---|---|---|
| A (chosen) | Explicit `CCA_OPERATIONAL_STORE` (`sqlite` \| `postgres` \| `mongodb`) plus existing `CCA_DB_URL` for SQLAlchemy backends and `CCA_MONGO_OPERATIONAL_URL` for the operational Mongo profile; factory branches on store | Clear profiles in `.env.example`; does not force Mongo URIs through SQLAlchemy `create_engine`; matches D45 |
| B | Overload only `CCA_DB_URL` (`sqlite://`, `postgresql+…`, `mongodb://`) | Mongo through SQLAlchemy is awkward; easy to break `get_engine()`; harder to document three profiles |
| C | Separate facade/API packages per backend | Violates D64; large rewrites — rejects the DoD |

## Current state (before this story)

| Piece | Today |
|---|---|
| Default URL | `get_settings()` → `sqlite:///{CCA_DATA_DIR}/operational.sqlite` when `CCA_DB_URL` unset |
| Postgres | Set `CCA_DB_URL`; same SQLAlchemy DAOs + Alembic (D23, D33); `tests/test_postgres.py` |
| Mongo operational | Not selected; complaint **data** Mongo is D10 / separate from admin store |
| `DaoObjectsFactory.init()` | Always registers SQLAlchemy DAO impls |

## Naming

| What | Name |
|---|---|
| Profile env | `CCA_OPERATIONAL_STORE` — optional; values `sqlite`, `postgres`, `mongodb` (trimmed, case-insensitive) |
| SQLAlchemy URL | `CCA_DB_URL` — SQLite default when unset; required Postgres URL when store is `postgres` |
| SQLite files dir | `CCA_DATA_DIR` — unchanged |
| Mongo operational URI | `CCA_MONGO_OPERATIONAL_URL` — required when store is `mongodb` |
| Settings field | `Settings.operational_store: Literal["sqlite","postgres","mongodb"]` |
| Mongo URI field | `Settings.mongo_operational_url: str \| None` |

## Resolution rules

1. If `CCA_OPERATIONAL_STORE` is set and non-blank after trim → must be one of the three values; else settings load fails with a clear error.
2. If unset:
   - blank/`CCA_DB_URL` unset → **sqlite**
   - URL dialect `sqlite` → **sqlite**
   - URL dialect `postgresql` / `postgres` → **postgres**
   - URL scheme `mongodb` / `mongodb+srv` → **mongodb** (convenience; still prefer explicit store)
   - anything else → fail
3. **postgres:** `CCA_DB_URL` must be present and a Postgres SQLAlchemy URL.
4. **mongodb:** `CCA_MONGO_OPERATIONAL_URL` must be present and non-blank; `CCA_DB_URL` is not used for the operational engine.
5. **sqlite:** if `CCA_DB_URL` blank, default file URL under `CCA_DATA_DIR` (existing behavior).

## Factory seam (D45)

- Facades/services/API continue to call `DaoObjectsFactory.get_*()` only.
- `DaoObjectsFactory.init()` registers **one** impl per DAO interface for the active store.
- **This story:** SQLAlchemy path unchanged for `sqlite` / `postgres`. If store is `mongodb`, `init()` fails fast with an explicit “not implemented — story #119” error (seam hook; no silent SQLAlchemy fallback).
- **Story #119:** add `mongo/` (or `impl/mongo_*`) DAO impls and register them when store is `mongodb`; lazy-import so `pymongo` is only required for that profile.
- No new facade packages (D64).

## Complaint data vs operational Mongo

| Store | Role | Selected by |
|---|---|---|
| SQLite / Postgres / operational Mongo | Admin/operational tables (D48) | D75 profile |
| MongoDB complaint database (`consumer_comp_db` name, D10/D21) | Bulk complaint documents | Unchanged; Airflow ingest — not this profile |

## Docs acceptance

- DESIGN.md gains **D75**.
- ARCHITECTURE.md §6 states the three local operational backends and the env switch.
- `.env.example` documents SQLite, Postgres, and MongoDB profiles (comments + empty vars).

## Out of scope

- Mongo DAO implementations and bootstrap (#119).
- npm/docker lite profiles (#120).
- Admin UI hardening (#121 / #122).
- DoD matrix run (#123).
- Cloud / RDS (M06).

## Self-review

- No placeholders; Mongo impl deferred with an explicit story pointer.
- Does not contradict D9/D45; refines them for M03 DoD.
- Scope is decision + env/settings validation + docs, not a backend rewrite.
