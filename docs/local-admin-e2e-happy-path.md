# Local Admin E2E happy path (M03-0012 / #122)

Prove **Admin UI → Middleware API → Airflow → callback APIs → operational DB → Admin UI refresh** on the **active DB profile**. Default is **SQLite** (D75: fewest containers). Do not invent MIO/ingest status in the UI — only show values returned by `GET /mios/status`.

## Automated smoke (CI / no Airflow)

From the repository root:

```bash
npm run local:e2e:happy-path:smoke
```

This runs `tests/test_e2e_happy_path_smoke.py`: mocked Airflow start → D60 callbacks → `GET /mios/status`, asserting status moves `requested` → `started` → `completed` with those exact strings.

## Live API probe (Middleware already running)

```bash
# API must be up (e.g. npm run local:handson:middlware:all:start)
npm run local:e2e:happy-path:probe
```

Optional full live path (Airflow required):

```bash
CCA_E2E_MODE=full CCA_CALLBACK_SECRET=… npm run local:e2e:happy-path:probe
```

## Full UI path (SQLite first)

### 1. Prereqs

- Clone with `.env` under `Middleware/ConsumerComplaintsHandsOn/` (from `.env.example`).
- Set `CCA_CALLBACK_SECRET` (Airflow must send the same value).
- Leave `CCA_OPERATIONAL_STORE` / `CCA_DB_URL` unset for **SQLite** default, or set them only when verifying another profile (#123).

### 2. Start runtime

```bash
npm run local:containers:all:start   # Airflow + local stack
npm run local:api:migrate
npm run local:portal:admin:with-api  # Middleware + Admin UI (proxy /api → :8000)
```

Open http://localhost:4200/ → **DataSets → Imports** (`/datasets/imports`).

### 3. Exercise

1. Confirm MIOs and workflows load (live API; errors show Middleware `detail`).
2. Start **`download_cfpb_all`** (or another seeded/enabled workflow) for a MIO.
3. Click **Refresh** while Airflow runs.

### 4. Expected status

| Phase | Exec / ingest status (from DB via API) |
|---|---|
| After Start (202) | `requested` until the first callback |
| Airflow running | `started` |
| Success | `completed` |
| Failure | `failed` |

Allowed moves follow D30 (`requested` → `started` → `completed`|`failed`, or `requested` → `failed`). The Admin UI must display these strings as returned — never invent enums client-side.

### 5. Common failures

| Symptom | Likely cause |
|---|---|
| 502 `engine start failed` | Airflow down or credentials/vars missing |
| Callbacks 401 | Wrong/missing `CCA_CALLBACK_SECRET` |
| UI error text from Middleware | Expected (#121); fix API/Airflow/DB, do not mask with fake status |

## Related

- Spec: `docs/Superpowers/specs/M03-0012-e2e-happy-path-design.md`
- Portal + API one-command: `npm run local:portal:admin:with-api`
- Pluggable store: D75 / story #116
