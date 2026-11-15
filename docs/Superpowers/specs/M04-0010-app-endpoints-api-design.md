# M04-0010 (#156) AppEndpoints list/read API

Builds on D85. Open to the Admin portal (no callback secret; D59). Responses never include secret values — only catalog fields (location ids, env-var *names*, credentials_ref *names*).

## Endpoints

- `GET /app-endpoints` — optional query: `category`, `enabled`, `name`. Ordered by category, name, id.
- `GET /app-endpoints/{id}` — one row or 404.

## Stack

Mirror D66: API → facade `app_ep` → service → `AppEndpointDao`. Map NOT_FOUND → 404; other failures → 500.

## Out of scope

Admin UI (#157), writes, DAG resolution.
