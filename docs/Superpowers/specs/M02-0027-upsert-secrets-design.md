# M02-0027 (#77) Push .env values to Airflow Variables (`upsert-secrets`)

Decisions: D5, D11, D26, D29, D35, D36, D37, D42, D45, D51, D54 and D59 in `Middleware/ConsumerComplaintsHandsOn/DESIGN.md`. Decided without the user present (D54 MVP); review and reverse if needed. D42 already defines the feature; this story builds it. No new DESIGN.md decision (D63 unused).

## Goal

`POST /management/airflow/upsert-secrets` (no body) copies each name listed in `CICD/Local/airflow/Airflow_Variables_Upsert.txt` from the process environment (filled from the git-ignored `.env` by `run_app.sh`) into Airflow Variables through Airflow 3.4's public REST API. One result per name (`created` / `updated` / `missing`), never a value. A missing name is reported, the rest still run, and the call is a failure. Protected by `CallbackSecretAuth` (`X-Callback-Secret`, D59).

## Approaches considered

| | Approach | Trade-off |
|---|---|---|
| A (chosen) | API → facade (one task) → service → private `httpx` Airflow Variables client (JWT then GET/POST/PATCH) | Matches every other story; mockable at the HTTP boundary; no new layer |
| B | Service shells out to `airflow variables set` inside Docker | Couples to compose; hard to test; fails in non-local layouts |
| C | Skip the facade and call the service from the API | Breaks the closed API→facades rule (import-linter) |

## Naming

| What | Name |
|---|---|
| API class (singleton, D29) | `AirflowUpsertSecretsApi` in `app/api/routers/airflow_upsert_secrets_api.py` |
| API models | `app/api/models/airflow_upsert_secrets_models.py`: `UpsertSecretResultOut`, `UpsertSecretsOut` |
| Facade | `AirflowUpsertSecretsFacade` / `AirflowUpsertSecretsFacadeImpl` / one task `AirflowUpsertSecretsCallServiceTask` |
| Service | `AirflowUpsertSecretsService` / `AirflowUpsertSecretsServiceImpl` |
| HTTP helper (private to services) | `AirflowVariablesClient` in `app/core/services/impl/airflow_variables_client.py` |
| DTOs | `app/core/common/dtos/airflow_upsert_secrets_dtos.py` and `airflow_upsert_secrets_facade_dtos.py` |
| Factory methods (D26) | `ServicesObjectsFactory.get_airflow_upsert_secrets_service()`, `FacadesObjectsFactory.get_airflow_upsert_secrets_facade()`, `ApiObjectsFactory.get_airflow_upsert_secrets_api()` |
| Names list (create in this story) | `CICD/Local/airflow/Airflow_Variables_Upsert.txt` |
| Settings | `airflow_api_base_url`, `airflow_api_username`, `airflow_api_password` (`repr=False`), `airflow_variables_upsert_path` |

No `init()` yet (D45 is after the MVP, D54): lazy singletons via package factories.

## Initial Variable names (MVP)

Committed list file (names only; `#` comments and blank lines ignored):

```text
# Copied into Airflow Variables by POST /management/airflow/upsert-secrets (D42). Never put values here.

CCA_CALLBACK_SECRET
CCA_DB_URL
```

| Name | Why |
|---|---|
| `CCA_CALLBACK_SECRET` | DAGs send `X-Callback-Secret` on callbacks (D59); the word `secret` makes Airflow mask it |
| `CCA_DB_URL` | DAGs read the operational database (D51); same name as Settings |

**Not upserted** (stay as API client Settings only): `CCA_AIRFLOW_API_BASE_URL`, `CCA_AIRFLOW_API_USERNAME`, `CCA_AIRFLOW_API_PASSWORD`. Putting Airflow's own login into Airflow Variables would be pointless and confusing.

`.env.example` lists every name above (and the three API client names) with empty values. Real values stay in the git-ignored `.env`.

`CCA_DB_URL` is not auto-masked by Airflow's name heuristics; accepted for MVP so the DAG and Settings share one name (D54). Masking can be revisited later without a DESIGN change.

## Configuration (`Settings`)

Read on every `get_settings()` call (same pattern as `CCA_CALLBACK_SECRET`):

| Env | Setting | Default |
|---|---|---|
| `CCA_AIRFLOW_API_BASE_URL` | `airflow_api_base_url: str` | `http://127.0.0.1:8080` (local compose UI/API) |
| `CCA_AIRFLOW_API_USERNAME` | `airflow_api_username: str` | `airflow` (compose `_AIRFLOW_WWW_USER_USERNAME`) |
| `CCA_AIRFLOW_API_PASSWORD` | `airflow_api_password: str` (`repr=False`) | `airflow` (compose `_AIRFLOW_WWW_USER_PASSWORD`) |
| (path, not env) | `airflow_variables_upsert_path: Path` | `PROJECT_ROOT.parents[1] / "CICD/Local/airflow/Airflow_Variables_Upsert.txt"` (repo root via pathlib, D35) |

Values to upsert are read with `os.environ.get(name)` (trimmed); unset or blank means **missing**. The process environment is the source of truth; `run_app.sh` exports `.env` into it. No `.env` file parser in the app.

## Airflow 3.4 REST (FabAuthManager / JWT)

Compose uses `FabAuthManager` and exposes the API on port 8080. Auth is JWT, not a session cookie:

1. `POST {base}/auth/token` with JSON `{"username","password"}` → `{"access_token":"..."}`.
2. Every Variables call: `Authorization: Bearer {access_token}`.
3. Detect create vs update: `GET /api/v2/variables/{key}` → `200` then `PATCH /api/v2/variables/{key}` with `{"key","value"}`; `404` then `POST /api/v2/variables` with `{"key","value"}`.

Client: **`httpx`** as a **runtime** dependency (today it is only in the dev group for `TestClient`). Timeouts: `httpx.Timeout(5.0, read=30.0)` (connect 5s, read 30s). One token per upsert call (fetch once, reuse for every name). Never log token, password, or Variable values.

## Layering

```text
AirflowUpsertSecretsApi
  → AirflowUpsertSecretsFacade (one task)
    → AirflowUpsertSecretsService.upsert
      → read names from the list file
      → for each name: env value or "missing"
      → AirflowVariablesClient.upsert_all (JWT + GET/POST/PATCH)
```

- Every method takes one ctx / DTO (D37).
- `AirflowVariablesClient` lives under `services/impl` (only the service impl imports it); not a DAO.
- The api package imports only common and facade interfaces (7 import-linter contracts kept).
- `ApiObjectsFactory` includes the router with `dependencies=[Depends(get_callback_secret_auth())]` like the status callback (D59).

## HTTP mapping

Service writes `ctx.resp.results` (name + outcome only) and returns:

| Condition | `ctx.resp.code` | HTTP |
|---|---|---|
| Every listed name `created` or `updated` | `SUCCESS` | **200** `UpsertSecretsOut` |
| At least one `missing` (Airflow calls for the others still ran) | `FAILURE` | **422** body still `UpsertSecretsOut` (results, never values); detail is not used — return the model via `JSONResponse` |
| List file missing/unreadable, or Airflow API credentials blank after trim, or JWT/Variables HTTP fails (connect error, non-success status, bad JSON) | `FAILURE` | **502** `{"detail":"airflow variables upsert failed"}` (safe; no values). Partial per-name results may be in logs as outcomes only, not in the 502 body |
| Unexpected exception | `FAILURE` | **500** `{"detail":"request failed"}` |
| Missing/wrong `X-Callback-Secret` | (auth dependency) | **401** (D59) |

422 (not 500) for missing env names: the operator's configuration is incomplete; the API itself is fine. 502 for Airflow: upstream dependency failed.

## Response shape

```json
{
  "results": [
    {"name": "CCA_CALLBACK_SECRET", "outcome": "updated"},
    {"name": "CCA_DB_URL", "outcome": "missing"}
  ]
}
```

`outcome` is exactly one of `created`, `updated`, `missing`. Never `value`, never the secret in headers of the response beyond the caller's own request.

## Logging

- Info: count of names processed and counts per outcome (no names required; if a name is logged, never its value).
- Warning on 502 paths: Airflow status code or "unreachable", never bodies that may contain Variable values.
- Never log `airflow_api_password`, JWT, env values, or Variable payloads.

## Tests

- Unit: list-file parsing (comments/blanks); env missing vs present; client GET→PATCH and GET→POST with a mocked `httpx` transport; service FAILURE when any missing; service 502 path when token fails.
- HTTP: right secret → 200/422 with results and no values in the body; wrong/missing secret → 401; `/health` still open.
- Singletons and factories; `lint-imports` 7 kept; regenerate `openapi.json`.
- No live Airflow in CI: mock HTTP only.

## Out of scope

- Airflow Connections (M03, D42(6)).
- Upserting API client credentials into Variables.
- `init()` on factories (D45).
- Renaming `CCA_DB_URL` for Airflow masking.
- Live compose integration test in CI.
