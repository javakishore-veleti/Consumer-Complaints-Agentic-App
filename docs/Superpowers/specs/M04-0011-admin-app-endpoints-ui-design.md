# M04-0011 (#157) Admin AppEndpoints thin UI for Imports

Builds on D85 + #156 (`GET /app-endpoints`). Admin portal only. Responses never include secret **values** — only catalog fields (ids, names, env-var **names**, `credentials_ref` **names**).

## Goal

Let operators see which AppEndpoints Imports can use, without leaving the Datasets area.

## Approaches considered

| | Approach | Trade-off |
|---|---|---|
| A | Separate Operations page | Reusable; farther from Imports |
| B (chosen) | Read-only panel on **Imports** page | Matches issue “for Imports”; same load lifecycle as MIO status |
| C | Only a select control with no table | Too thin; hard to verify from/to |

## Design

1. **Core helper** `Portals/.../src/app/core/app-endpoints.ts` — `loadAppEndpoints(http, ctx)` → `GET {apiBaseUrl}/app-endpoints` with optional `category` / `enabled`. Ctx pattern (D37-style portal helpers): `req` / `resp.entries` / `resp.error`; return `SUCCESS`/`FAILURE`. Map only safe fields from `AppEndpointOut` (never invent a `value` field).
2. **Imports page** — on init (alongside MIO status), load endpoints (default: no filter, or `enabled=true`). Render a compact table/list above the MIO accordion: name, category, from (location id **or** env var name), to (same), credentials_ref (name or “—”), enabled. `data-testid` hooks for tests. Error alert if load fails; empty state if none.
3. **Secrets rule** — UI copy notes that values are never shown. Do not bind or display any secret payload. `credentials_ref` is a **name** only.
4. **No writes** — list/read only. No create/edit. Selection that drives DAG start stays for later stories (#161); this story is browse + prove the API is usable from Admin.
5. **Tests** — unit test helper (HttpClientTestingModule) + Imports page spec: expects `GET /api/app-endpoints` (or whatever `environment.apiBaseUrl` + path is) and renders at least one row without secret values.

## Out of scope

Writes, DB Ingest screen (#160), DAG resolution (#161), vector index UI (#164).
