# M58-0001 Admin Schemas + Iceberg foundational schema — design

**Story:** #400 · **Date:** 2026-11-20

## Problem

Operators were told to run `npm run local:iceberg:apply-*-ddl` / hydrate for lakehouse setup. That conflates start/stop with data-plane schema/data work. Foundational schema should be Admin → Middleware → Airflow, like Lakehouse hydrates.

## Decisions

1. **Foundational** = data-plane stores (Iceberg now). **Not** CCA operational Postgres (Alembic stays on `npm run local:api:migrate` so Workflow Logs exist).
2. **One WF per store.** Iceberg WF applies **all zones in one run**: Raw → Refined → Taxonomy → Curated (idempotent DDL).
3. Mongo foundational WF: **skip** until there is real data-plane schema beyond API bootstrap indexes.
4. Admin **Schemas** left-nav (sibling of Lakehouse). Filter workflows whose names start with `apply_` (or exact `apply_iceberg_foundational_schema`).
5. Hydrate stays on **Lakehouse**.
6. Runbook: remove operator iceberg npm DDL/hydrate; point to Schemas then Lakehouse. Keep npm for containers/API/Admin/migrate/Airflow. CLI scripts may remain for CI.

## Shape

| Piece | Name |
|--------|------|
| DAG / workflow | `apply_iceberg_foundational_schema` |
| Script | `apply_iceberg_foundational_ddl_incontainer.sh` (+ host wrapper chaining zone applies) |
| Compose | Mount `./sql` → `/opt/cca/iceberg/sql` |
| Seed | Alembic 0033 + Mongo bootstrap; bind to 3m MIO |

## Out of scope

Mongo/S3/Cosmos foundational WFs; stripping CI `local:iceberg:prove-*` scripts.
