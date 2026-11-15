# AppEndpoints table/DAO/seed Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship `app_endpoints` (D85) with Alembic `0012` seed, SQLAlchemy + Mongo DAOs, and tests for story #155.

**Architecture:** Mirror `datasets_location` / `mios_workflows`: one SQLAlchemy DAO for sqlite/postgres, parallel Mongo DAO + bootstrap seed, factory registration, no FKs.

**Tech Stack:** Alembic, SQLAlchemy, Mongo operational store (D79), pytest, existing return codes / SingletonMeta.

## Global Constraints

- Open story #155 on GitHub Milestone M04; Superpowers only — no vibe coding.
- Seed UUID: `ccbce57d-bd9f-56fe-a258-fa2deb9dd393` (`uuid5` of `ccaa/m04-0009/ep-cfpb-source-http-local`).
- Categories only: `source`, `ingest`, `index`, `db`.
- Never store secret values; `credentials_ref` is a name.

---

### Task 1: Types + DTOs + interface

- [ ] Add `AppEndpointCategory` to `app_types_constants.py`
- [ ] Add `app_endpoint_dtos.py` (Record/Req/Resp/Ctx)
- [ ] Add `app_endpoint_dao.py` interface
- [ ] Extend `test_app_types_constants.py` for the new enum
- [ ] Commit: `M04-0009 #155: add AppEndpoint types and DAO interface`

### Task 2: Model + Alembic 0012

- [ ] Add `AppEndpointModel` to `models.py`
- [ ] Add `0012_create_app_endpoints_and_seed.py` (create + seed)
- [ ] Add schema tests in `test_schema.py` (columns, xor, seed row, downgrade)
- [ ] Update `test_postgres.py` admin table sets to include `app_endpoints` where `mios_workflows` is asserted
- [ ] Commit: `M04-0009 #155: alembic 0012 app_endpoints + seed`

### Task 3: SQLAlchemy DAO + tests

- [ ] Implement `sqlalchemy_app_endpoint_dao.py`
- [ ] Register in `objects_factory.py` (sqlite/postgres branch)
- [ ] Write `tests/test_app_endpoint_dao.py` (happy path + invalid/conflict/not found)
- [ ] Update `test_singletons.py`
- [ ] Run `npm run local:api:lint` and `npm run local:api:test`
- [ ] Commit: `M04-0009 #155: SQLAlchemy AppEndpointDao`

### Task 4: Mongo DAO + bootstrap

- [ ] Implement `mongo_app_endpoint_dao.py`
- [ ] Update `bootstrap.py` (COLLECTIONS, indexes, seed)
- [ ] Register Mongo branch in factory
- [ ] Assert seed in `test_mongodb_operational_store.py` if useful
- [ ] Run tests again
- [ ] Commit: `M04-0009 #155: Mongo AppEndpointDao + bootstrap seed`

### Task 5: DESIGN / ARCHITECTURE / PRODUCT_FEATURES

- [ ] Add D85 to DESIGN.md; update catalog / D76 schema lists
- [ ] Update ARCHITECTURE.md admin schema list
- [ ] Update PRODUCT_FEATURES F5 + close open Q1
- [ ] Commit: `M04-0009 #155: document D85 AppEndpoints`

### Task 6: Finish

- [ ] Verification: lint + full pytest green
- [ ] Merge/finish branch onto main; push
- [ ] `/ccaa-story-complete 155`
