# M02-0009 (#44) Shared-secret authentication for callbacks

Decisions: D5, D11, D26, D29, D35, D36, D37, D42, D45, D54 and D59 in `Middleware/ConsumerComplaintsHandsOn/DESIGN.md`. Decided without the user present (D59); review and reverse if needed.

## Goal

The endpoints Airflow calls are protected by one shared secret. A missing or wrong secret is 401. The secret is configuration and is never in the repository. This story builds the check and proves it on a router that exists only in the tests; it adds no endpoint. The status callback (#43) is the first real router to use it.

## Naming

| What | Name |
|---|---|
| The check (a FastAPI dependency, a singleton) | `CallbackSecretAuth` in `app/api/security/callback_secret_auth.py` (new package `app/api/security/`) |
| Factory method | `ApiObjectsFactory.get_callback_secret_auth() -> CallbackSecretAuth` |
| Header Airflow sends | `X-Callback-Secret` (constant `CALLBACK_SECRET_HEADER` in the same module) |
| Environment variable | `CCA_CALLBACK_SECRET` (the `CCA_` prefix of the other settings; the word "secret" makes Airflow mask it when it becomes a Variable, D42) |
| Setting | `Settings.callback_secret: str \| None` in `app/core/common/config.py` |

## Mechanism

- `get_settings()` reads `CCA_CALLBACK_SECRET` on every call, like `CCA_DB_URL`, trims it, and turns an unset or blank value into `None` ("not configured"). The field has `repr=False`, so printing or logging the settings never shows it.
- `CallbackSecretAuth.__call__(self, request: Request) -> None` is the dependency. It takes one object, the FastAPI `Request` (D37), reads the setting on each call, and reads the header from the request.
  - Not configured: refuse (401). **Fail closed:** a forgotten setting never leaves an endpoint open, and an empty header can never match an empty secret.
  - Configured: compare the header with the secret using `hmac.compare_digest` on latin-1 bytes (constant time, so the response time does not leak how much of a guess was right; bytes because `compare_digest` raises on a `str` with non-ASCII characters; latin-1 because Starlette decodes the header bytes as latin-1, so a latin-1 secret matches consistently). A configured secret that latin-1 cannot encode never matches: it is refused with 401 and raises nothing (fail closed). A missing header is compared as the empty string and fails.
  - Match: return `None` and the endpoint runs. No match: 401, and the endpoint never runs.
- The class holds no state (D27). It is a singleton through `SingletonMeta` (D26), handed out by the api package's `objects_factory` as a lazy static method; there is no `init()` yet (D45 is after the MVP, D54).
- Starlette treats header names case-insensitively, so `x-callback-secret` works too. The value is compared exactly (case sensitive; the HTTP server has already removed surrounding spaces).

## The 401 response

Every refusal that reaches the check is the same, so a caller learns nothing about why (missing, wrong or not configured):

- Status `401 Unauthorized`.
- Body `{"detail": "missing or wrong callback secret"}` (FastAPI's `HTTPException` shape, like every other error of the API).
- Header `WWW-Authenticate: X-Callback-Secret` (RFC 9110 requires a challenge on 401; the challenge names the header to send).

One case never reaches the check: FastAPI parses the JSON body before it runs the router's dependencies, so on a protected route with a body, a malformed JSON body without the secret is refused with `422` before the check and the endpoint never runs. A valid body, or a body that is JSON of the wrong shape, reaches the check and gets the 401 without the right secret. This is accepted and pinned by tests (`tests/test_callback_secret_api.py`); a later story (#43) may move the check ahead of parsing if that matters.

## Logging

- Each refusal logs one warning on the module logger: `callback refused: CCA_CALLBACK_SECRET is not set, so every callback is refused` or `callback refused: missing or wrong X-Callback-Secret header`.
- Neither the configured secret nor the value a caller sent is ever logged, returned or put in an exception message.

## How later stories attach it

The check is attached to a whole router when `ApiObjectsFactory._build_app` includes that router, never per endpoint and never inside the router class (a router class importing the factory would be a circular import):

```python
app.include_router(
    StatusCallbackApi().router, dependencies=[Depends(ApiObjectsFactory.get_callback_secret_auth())]
)
```

- **#43 (status callback endpoint):** its router is included this way.
- **#77 (`POST /management/airflow/upsert-secrets`, D42):** "protected by the shared secret of the callback endpoints"; included the same way.
- **#45 (read MIO status endpoint):** DESIGN section 4.2 says the admin portal calls it, and a browser cannot keep a shared secret, so it stays open like the other portal endpoints unless its story finds that Airflow calls it. Protecting portal endpoints is out of scope here.
- Router-level protection does not change `openapi.json` (no security scheme is declared), so `tests/test_openapi_spec.py` stays as it is. Declaring the header in the OpenAPI spec (a Swagger "Authorize" button) can come with #43 if wanted.

## What stays open

`/health`, `/docs`, `/openapi.json` and `/data-ingest-logs` stay open: none is called by Airflow, and the start script polls `/health`.

## Configuration

- The value lives only in the git-ignored `Middleware/ConsumerComplaintsHandsOn/.env` (the root `.gitignore` ignores `.env` at any depth). A committed `Middleware/ConsumerComplaintsHandsOn/.env.example` lists `CCA_CALLBACK_SECRET=` with an empty value and how to generate one (`openssl rand -hex 32`) (D42).
- `run_app.sh` exports every name set in `./.env` before it starts the API (`set -a; source ./.env; set +a`), and its header comment lists `CCA_CALLBACK_SECRET`. Without `.env`, the variable can still be exported in the shell.
- `ARCHITECTURE.md` section 8 (local environment) gets a short paragraph on `.env`, `.env.example` and the secret. The README files hold no configuration today, so they are not changed.

## Tests

- `tests/test_callback_secret_auth.py` (the check on its own, calling the singleton with a Starlette `Request` built from a scope): the setting is trimmed and blank means `None`; `repr(get_settings())` does not show the secret; the right secret passes; a lowercase header name passes; a missing header is 401 with the detail and the `WWW-Authenticate` header; wrong values (another value, empty, one character more, one fewer, other case, a non-ASCII character) are 401 (the non-ASCII value raises no `TypeError`); a latin-1 secret (`caf\u00e9-fake`) matches when sent as latin-1 bytes; a configured secret latin-1 cannot encode (`\u20ac-fake`) is 401 and raises nothing; with no secret configured, no header, an empty header and any header are all 401; a blank configured secret does not accept an empty header; the setting is read on every call; each refusal logs its warning and never the configured secret or the sent value.
- `tests/test_callback_secret_api.py` (through HTTP with `TestClient`): a throwaway `FastAPI` app built in the test includes a throwaway router at `/test-callbacks/ping` with the check attached at include time, exactly as #43 will do it. The right secret reaches the endpoint (200); a missing, wrong or empty header is 401 with the body and challenge above, the endpoint function never runs, and the response never contains the secret; the secret sent as `Authorization: Bearer ...` is 401; on a body-taking route, a valid body without the right secret is 401 and a malformed JSON body is 422, and the endpoint runs in neither case; with the secret unset or blank, the router is closed. With the real app (`client` fixture), `/health` and `/data-ingest-logs` answer without the header, with and without a configured secret.
- `tests/test_singletons.py`: the factory method returns the same object, typed as `CallbackSecretAuth`, and `CallbackSecretAuth()` is a singleton.
- Unchanged and still green: `tests/test_ctx_only_signatures.py` (the dependency takes one `Request`; the factory method takes nothing), `tests/test_import_contracts.py` (the api package imports only `app.core.common`; 7 contracts kept), `tests/test_openapi_spec.py`, `tests/test_portability.py`.

## Out of scope

- Rotating secrets (two valid at once) and one secret per caller.
- Protecting portal endpoints (comes with user management).
- Any new endpoint in the app; the protected router lives only in the tests.
- The Airflow side that sends the header: story #59 (report started, completed and failed to the API) sends `X-Callback-Secret` on every callback; the value reaches Airflow as a masked Variable through #77 (D42), or by hand in Airflow until #77 is built.
- An OpenAPI security scheme for the header.
