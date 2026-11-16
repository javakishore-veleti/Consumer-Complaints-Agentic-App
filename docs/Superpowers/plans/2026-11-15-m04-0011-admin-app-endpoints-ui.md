# M04-0011 (#157) Admin AppEndpoints thin UI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Show AppEndpoints from `GET /app-endpoints` on the Admin Imports page without ever displaying secret values.

**Architecture:** Portal ctx helper (mirror `mio-status` / `airflow-upsert-secrets`) + read-only panel on `ImportsPageComponent`. List/read only.

**Tech Stack:** Angular 22 standalone, HttpClient, Jasmine/Karma, TailwindAdmin chrome.

## Global Constraints

- Never show or store secret values; only catalog fields (ids, names, env-var names, credentials_ref names).
- `environment.apiBaseUrl` is `/api`; request path `/app-endpoints`.
- Follow existing Imports / Sync secrets patterns (signals, `data-testid`, SUCCESS/FAILURE).
- Commit message form: `M04-0011 #157: <imperative summary>`.

---

## Task 1: Core helper + unit test

**Files:**
- Create: `Portals/consumer-complaints-admin/src/app/core/app-endpoints.ts`
- Create: `Portals/consumer-complaints-admin/src/app/core/app-endpoints.spec.ts`

- [ ] Write failing tests: GET `/api/app-endpoints`, maps safe fields, FAILURE on HTTP error, JSON has no `value` key invented
- [ ] Implement `loadAppEndpoints(http, ctx)` with optional `category`/`enabled` query
- [ ] Run portal unit tests for this file; commit

## Task 2: Imports page panel + specs

**Files:**
- Modify: `imports-page.component.ts` / `.html` / `.spec.ts`

- [ ] Update existing specs so init also flushes `/app-endpoints` (empty array OK)
- [ ] Add failing test: renders endpoint row from GET response (name/category/from/to); no secret values
- [ ] Implement panel + load on init; error/empty states
- [ ] Run Imports specs; commit

## Task 3: Verify + finish

- [ ] Run full portal test suite for touched specs
- [ ] Update PRODUCT_FEATURES F5 note if needed (thin UI done)
- [ ] Milestone log / story-complete / merge to main via finishing-a-development-branch
