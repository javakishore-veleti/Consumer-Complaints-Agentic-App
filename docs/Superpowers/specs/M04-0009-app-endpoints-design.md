# M04-0009 (#155) AppEndpoints table, DAO, and local seed

Decisions: D49, D57, D63, D75, D79 and **D85** in `Middleware/ConsumerComplaintsHandsOn/DESIGN.md`. Next free decision after this story is **D86**.

## Goal

Add catalog table `app_endpoints` so Imports (and later ingest/index) can resolve **from → to** configs by category (`source` / `ingest` / `index` / `db`), referencing `datasets_location` ids and/or env-var **names** only. Local-first seed: CFPB HTTP → local (D63).

## Context (already built)

| Piece | Where |
|---|---|
| Locations hold path XOR `local_env_var_name` | D57 / `datasets_location` |
| Download uses HTTP source + local landing | D63 |
| SQLAlchemy + Mongo DAO parity | D75 / D79 |
| Alembic head | `0011` (`mios_workflows`) |
| API / Admin UI for AppEndpoints | **Out of scope** (#156 / #157) |

## Approaches considered

| | Approach | Trade-off |
|---|---|---|
| A | Embed from/to only in workflow `config` JSON | Fast; not browsable; duplicates across MIOs |
| B (chosen) | Catalog table `app_endpoints` + DAO + seed | Matches F5; reusable; same pattern as locations |
| C | Hard-code endpoints in Angular | Skips catalog; breaks engines |

## Decision D85 (summary)

1. **Table `app_endpoints`** in `consumer_comp_admin_db` (Mongo collection same name):  
   `id`, `name` (unique), `category` (`source`\|`ingest`\|`index`\|`db` via `AppEndpointCategory`),  
   `from_dataset_location_id` XOR `from_env_var_name`,  
   `to_dataset_location_id` XOR `to_env_var_name`,  
   optional `credentials_ref` (name only, same regex as locations), `description`, `enabled` (default true), `created_at`, `updated_at`.  
   No DB FKs. Indexes: `uq_app_endpoints_name`, `ix_app_endpoints_category`, xor checks.
2. **DAO** `AppEndpointDao`: create/get/list/update/delete; SQLAlchemy + Mongo; factory registration. Validate category enum; xor sides; location ids must exist (`NOT_FOUND`); name conflict → `CONFLICT`.
3. **Seed** (Alembic `0012` + Mongo bootstrap), fixed UUID5 `ccaa/m04-0009/ep-cfpb-source-http-local` → `ccbce57d-bd9f-56fe-a258-fa2deb9dd393`:  
   name `cfpb_source_http_to_local`, category `source`, from HTTP location id, to local location id, enabled.
4. **Docs:** DESIGN D85 + catalog row; ARCHITECTURE admin schema list; PRODUCT_FEATURES F5 + close open Q1.
5. **Not in this story:** HTTP API, Admin UI, DAG resolution (#156–#157, #161).

## Tests

- Schema: table/constraints/seed on SQLite; postgres admin table set includes `app_endpoints` when those tests run.
- DAO: create/list/filter/update/delete; bad category / missing xor / unknown location / duplicate name.
- Mongo bootstrap seeds the same endpoint id.
- Singletons / types: `AppEndpointCategory`, factory getter.

## Out of scope

List/read API (#156), Admin UI (#157), ingest/index seed rows, complaint-Mongo env naming (#158).
