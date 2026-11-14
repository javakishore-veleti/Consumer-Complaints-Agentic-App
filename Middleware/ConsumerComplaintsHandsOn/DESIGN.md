# Design

Detailed decisions behind the [architecture](ARCHITECTURE.md). Features are in [PRODUCT_FEATURES.md](../../Docs/PRODUCT_FEATURES.md).

Every item is marked:
- **Decided**: agreed in design discussion.
- **Proposed**: suggested, not yet confirmed. Treat as a default that can change.
- **Open**: needs a decision.

---

## 1. Decided

| # | Decision |
|---|---|
| D1 | Layered architecture after Neal Ford, **closed layers**, with **services as the single open layer**. Flow: `api -> facades -> daos or services`. |
| D2 | Every boundary is crossed through an **interface**. The API sees facade interfaces; facades see service and DAO interfaces. |
| D3 | Each package has `<interface>` in the package and implementations in `impl/`. |
| D4 | **Every package has an `objects_factory.py`** (api, common, facades, services, dao). It is the only module that imports `impl/`. |
| D5 | **No method takes individual arguments.** Python and Angular alike take one `XxxCtx` (containing `XxxReq` and `XxxResp`) and return an **integer**. The code values are defined later. |
| D6 | Each facade has a **dedicated task interface**; every task of that facade implements it, takes only that facade's ctx, returns an integer. The facade loops over its tasks and has no logic of its own. |
| D7 | **One DAO per table** (separate DAOs for `system_datasets`, `data_ingest_log`, ...). |
| D8 | Python ORM: **SQLAlchemy**. Schema versioning: **Alembic** (chosen over Liquibase, knowing Alembic lacks checksums, preconditions, contexts and a lock table). |
| D9 | **SQLite now** for operational data, replaceable (Postgres or another database) with the fewest code changes. |
| D10 | **MongoDB** holds the actual complaint data (local Docker container). |
| D11 | **SQLite is written only by the API.** Airflow reports progress by calling API endpoints. |
| D12 | The download is **asynchronous**: the facade triggers an Airflow DAG and returns. A separate DAG ingests into MongoDB. |
| D13 | DB Ingest is started **manually** from its own screen (left nav, parallel to Imports), not automatically after a download. |
| D14 | One common log table `data_ingest_log` with a `purpose` column, plus a `system_datasets` table with the current state. |
| D15 | **One endpoint starts any download**, taking a `usecase`. **One endpoint receives Airflow status updates**, taking `usecase` and `status`. |
| D16 | The dataset is **never committed to the repository**. Download reads from a **configured location type and path**: local path, GitHub repo URL, Google Drive, AWS S3, Azure Blob, GCP Cloud Storage. |
| D17 | Locally the migrations run from the start script before the API starts; in the cloud they will run from a manually triggered workflow (M03, D34). |
| D18 | One OpenAPI (Swagger) specification for the whole hands-on project. |
| D19 | Local: 3 months dataset. Cloud: All dataset. Same code, different configuration. |
| D20 | MongoDB bulk ingestion by the Airflow job directly; PySpark only if measurements justify it. |
| D21 | Three schemas: **`consumer_comp_db`** (consumer complaints area: `data_ingest_log`, later `system_datasets`; also the MongoDB database name), **`consumer_compl_intellect_db`** (the Intellect app's own area), **`consumer_comp_users_db`** (user management). Names are exactly as given. On SQLite each schema is an attached database file named after it; on Postgres and similar they are real schemas. |
| D22 | Return codes: `0` success, `1` failure, `2` not found, `3` invalid input (`app/core/common/return_codes.py`). More are added as needed. |
| D23 | Migrations are written with Alembic's Python operations (`op.create_table`), not raw SQL, so the same migration runs on SQLite and Postgres. `alembic upgrade head --sql` prints the SQL when a SQL file is needed. |
| D24 | The facade **stops at the first task that does not return success** and returns that code. |
| D25 | A facade task gets the DAO from the DAO package's `objects_factory`. Factory methods take no arguments (exempt from the ctx rule). The database engine is cached in `dao/impl/database.py`. |
| D26 | **Every class in `api`, `facades`, `services` and `dao` is a singleton.** Each interface declares `metaclass=SingletonMeta` (`core/common/singleton.py`, thread-safe, re-entrant), so every implementation inherits it. Each package's `objects_factory.py` is a class with **static methods that return the singleton, typed as the interface** (`DaoObjectsFactory.get_data_ingest_dao()`, `FacadesObjectsFactory.get_data_ingest_facade()`, `ApiObjectsFactory.get_app()`, `ServicesObjectsFactory`). |
| D27 | Consequence of D26: these classes hold **no per-request state**; it lives in the ctx. So tasks take no constructor arguments and read what they need from the ctx (for example `ctx.operation`, set by the facade). Req, Resp, Ctx, ORM table classes and API request bodies are data, not singletons. |
| D28 | **One class per file, and a task is its own file.** Facade tasks live in `facades/impl/tasks/`, one `.py` per task, named `<facade>_<what>_task.py`. Keeps files small and avoids static-analysis (Sonar) findings on large modules. Validation is split into small methods instead of one long branch chain. |
| D29 | **The API is a class too.** Each endpoint group is a singleton class (`DataIngestApi`) that owns an `APIRouter` and registers its methods in the constructor. Each endpoint method takes one request model that FastAPI fills from the path, query string or body, and builds the facade ctx from it (D37). |
| D30 | **Status changes follow fixed rules**: requested -> started -> completed or failed, and requested -> failed. Completed and failed are final. The same status again is accepted and changes nothing (Airflow retries). Anything else returns `CONFLICT` (4), HTTP 409. The rule is checked and written in one DAO transaction, so concurrent callbacks cannot race. A new row is always `requested`. |
| D31 | **Layer rules are enforced by import-linter** (`.importlinter`, run by `lint-imports`, by pytest and in CI): layers api -> facades -> services -> dao, common depends on nothing, the API talks to facades only, nobody imports another package's `impl/`. |
| D32 | **One OpenAPI file**, `Middleware/ConsumerComplaintsHandsOn/openapi.json`, generated from the code (`npm run local:api:openapi`). A test fails when the committed file is out of date. |
| D33 | **Postgres is verified** by `tests/test_postgres.py` (migrations up, down, up, and the DAO) when `CCA_TEST_POSTGRES_URL` is set; CI runs it against a Postgres service. Migrations use Alembic batch mode on SQLite. |
| D34 | **Cloud migrations are deferred to the cloud milestone (M03).** A manually triggered GitHub Actions workflow that runs the migrations against AWS, Azure or GCP databases is planned there, not built now; the first version was removed from the repo. The questions to settle then: how the runner reaches a private database (self-hosted runner, tunnel or allow-list) and where the credentials live (GitHub environment secrets). | The current milestone is local development only. |
| D35 | **Nothing machine- or person-specific is committed.** Paths come from `pathlib` (`Path(__file__).resolve()`) or `dirname "$0"`, never typed in; owner and repository names are never hardcoded (tools read them from the git remote). `tests/test_portability.py` fails on a home-directory path or a GitHub owner URL. | So any teammate can clone the repo to any folder on any OS and everything runs. |
| D36 | **Scratch space is `runtime_data/tmp/` at the repository root (git-ignored), not `/tmp`.** Pytest temp folders (`runtime_data/tmp/pytest`) and local helper scripts and state (`runtime_data/tmp/...`) live there. The operational SQLite files stay in `Middleware/ConsumerComplaintsHandsOn/.data/` (also ignored). | Everything a run produces stays inside the repository folder, can be deleted in one go, and never leaks into shared system folders. |
| D37 | **Every function and method takes nothing or exactly one ctx / request / DTO object, never separate arguments and never a bare value.** That includes API endpoints (each takes one request model that FastAPI fills from the path, query string or body), private helpers and test helpers. The result code also travels in `ctx.resp.code`, so the API reads it from the ctx. Only signatures a library dictates are exempt (Alembic's `_include_name`, SQLAlchemy's connect-event hook, the metaclass `__call__`), each listed with its reason in `tests/test_ctx_only_signatures.py`, which fails on any other violation. | Adding a field never changes a signature, every layer reads the same way, and the rule is enforced by a test instead of by memory. Side effect: the list endpoint's filter is now `?status=` (it was `?status_=` by accident of an argument name). |
| D38 | **M01 is local development only.** Everything runs on the laptop (SQLite, local Airflow and MongoDB in Docker, local files and URLs as sources). AWS, Azure and GCP work (cloud databases and migration workflow, S3, Azure Blob, GCS and Google Drive sources) is the next milestone (M03, "Cloud Deployment"). The code keeps its seams (database URL in settings, one class per source type), so adding the cloud is additions, not rewrites. | Finish a working local product first. |
| D39 | **A transaction that several DAO calls share is opened by a service, through the `TransactionDao`.** `begin` puts an opaque handle on a `TransactionCtx`; the service puts that on the ctx of each DAO call (every DAO ctx extends `TransactionalCtx`); the DAOs then join it and do not commit; the service commits, or rolls back when any step does not return SUCCESS. With no transaction on the ctx a DAO call runs and commits on its own. | Business rules that touch two tables stay in the services layer, the DAOs stay one per table, and nothing above `dao/impl` sees SQLAlchemy. `tests/test_dataset_status_service.py` proves it: if the second write fails, the first is not kept. |
| D40 | **`system_datasets` has one row per dataset and stage; the dataset row follows the log row.** Usecases map to rows (`download_3_months`, `download_all`, `ingest_3_months`, `ingest_all`). Requesting a run writes a `requested` log row and sets the row to `running`; a second request while it is running is a CONFLICT. A report (`started`, `completed`, `failed`) changes the newest log row of the usecase (D30 rules) and the dataset row together; the same report twice is accepted; a report carrying a `run_id` that differs from the newest row's `run_id` is a CONFLICT (an older run must not change the newest one). | Airflow retries callbacks and can be late, and the portal must always show one consistent state. |

## 2. Conventions in detail

### 2.1 Ctx, Req, Resp
- `XxxReq`: what the caller sends. `XxxResp`: what comes back. `XxxCtx`: holds both.
- Results are written into `ctx.resp`; the integer return is only the outcome code (success, failure, or another code defined later).
- **Proposed:** the ctx also has a working area for values passed between tasks (for example the log row ID task 1 creates and task 3 needs), so `resp` holds only what the caller receives. **Open.**
- **Decided:** every Req/Resp/Ctx type lives in the shared `common/dtos`, never in `facades/`, `services/` or `dao/`, so a lower layer never imports an upper one.
- **Decided:** each table has one reusable DAO (create, read, update, delete) with its **own dedicated ctx**, not the facade's ctx. First one: `DataIngestCtx` (with `DataIngestReq` / `DataIngestResp`) for `data_ingest_log`. The DAO's methods take only that ctx, so any facade can use the DAO. Class names do not carry a "Crud" word.
- **Decided:** a facade's ctx class carries the DAO's ctx as an **additional member variable** (`data_ingest_ctx`). A facade task builds the `DataIngestCtx`, stores it on the facade ctx, and calls the DAO with it. This replaces the earlier idea of passing the facade's ctx all the way to the DAO, and removes the need for a shared base ctx.
- **Decided (D25):** the task gets the DAO singleton from the DAO's `objects_factory`; it is not stored on the ctx.
- **Implemented:** `DataIngestCtx` / `DataIngestReq` / `DataIngestResp` / `DataIngestRecord` in `common/dtos/data_ingest_dtos.py`; `DataIngestFacadeCtx` / `Req` / `Resp` in `data_ingest_facade_dtos.py`.

### 2.2 Interfaces and factories
- Import rule: you may import a package's interface and its `objects_factory`; you may never import its `impl/`.
- A factory picks the implementation from configuration. **Decided (D25, D26):** factories are classes with static methods that take no arguments and return the singleton, typed as the interface.
- **Implemented:** `tests/test_layering.py` checks the import rules by reading the source. **Proposed:** replace it with `import-linter` in the build.

### 2.3 Facade tasks
- The facade (a singleton) declares its ordered task list once, in its constructor; it sets `ctx.operation` and runs the tasks in order. Tasks are singletons too (D26, D27).
- **Decided (D24):** on a non-success return the facade stops and returns that code.
- **Implemented** for the data ingest facade, for every operation: `ValidateRequestTask` -> `PrepareDaoCtxTask` -> `CallDaoTask` -> `CollectResponseTask`.

### 2.4 ORM and transactions
- SQLAlchemy table classes stay inside `dao/impl/`. DAOs convert them to and from plain Req/Resp objects.
- Updating `data_ingest_log` and `system_datasets` together is **one transaction** (D39). **Implemented:** `DatasetStatusService` (in `services/`) opens a transaction through the `TransactionDao`, puts it on the ctx of both DAO calls, and commits or rolls back.
- Use application-generated IDs (UUID strings) and UTC timestamps, so nothing is tied to one database.

## 3. Operational data model (SQLite)

### `data_ingest_log` (append-only history) — Implemented (schema `consumer_comp_db`, migration `0001`)
The DAO sets `requested_at` on create, `started_at` when the status becomes `started`, and `finished_at` when it becomes
`completed` or `failed`. The API exposes plain create / get / list / update / delete under `/data-ingest-logs`; the
use-case endpoints of section 4.2 will sit on top of this table.
Status changes are enforced (D30).
| Column | Meaning |
|---|---|
| id | application-generated ID |
| purpose | the usecase, a fixed set (see 4.1) |
| status | requested, started, completed, failed |
| run_id | Airflow run ID, used to match callbacks |
| message | error text on failure |
| requested_at, started_at, finished_at | UTC timestamps |
| (optional) source type / path | where the data came from |

### `system_datasets` (current state) — Implemented (schema `consumer_comp_db`, migration `0002`)
**Decided (D40):** one row per dataset and stage (not JSON, not independent columns).
- Adding a dataset or stage is just new rows, no migration, no JSON read-modify-write race between two callbacks. Migration `0002` seeds the four rows as `not_started`.

| dataset | stage | status | last log row | updated |
|---|---|---|---|---|
| 3_months | download | not_started / running / completed / failed | log id | UTC time |
| 3_months | db_ingest | ... | ... | ... |
| all | download | ... | ... | ... |
| all | db_ingest | ... | ... | ... |

- A `usecase` maps to exactly one row (dataset + stage), and is the value of the log's `purpose`.
- Status is a value, not a boolean: the UI must tell not started, running, completed and failed apart. The dataset row follows the log row: requested and started show as running, completed as completed, failed as failed (D40).
- **Open:** a new download of the 3-month dataset resets its ingest status (leaning yes; not done yet). **Open:** record the absolute date range covered.

Users and execution logs are further SQLite tables, to be defined. The log table's name says "ingest" but also records downloads; `data_pipeline_log` would be clearer (**Open**, naming only).

## 4. API contract (Proposed; one OpenAPI spec)

### 4.1 Usecases
A fixed set; each maps to one `system_datasets` row. Illustrative: download for 3 months, download for all, ingest for 3 months,
ingest for all. Exact names **Open**.

### 4.2 Endpoints
| Purpose | Called by | Input |
|---|---|---|
| Start a download | admin portal | `usecase` |
| Start a DB ingest | admin portal | `usecase` |
| Status update (Airflow callback) | Airflow | `usecase`, `status` (started, completed, failed); **Open:** also optional `run_id` and `message` (recommended) |
| Read dataset status | admin portal | none (returns the accordion data) |

- The callback endpoints need a **shared secret**; the caller is Airflow, not a person.
- Allowed status changes: requested -> started -> completed or failed. Anything else (duplicate, out of order) is ignored or rejected, because Airflow retries.
- **Open:** one "completed" endpoint with an outcome, or separate completed and failed endpoints. **Open:** code-first (FastAPI generates the spec, exported to a committed file) versus spec-first, and where the file lives. Leaning: code-first with an exported file.
- The DAG's final task must run even when earlier tasks fail, so a crashed run does not leave the row stuck on "running".

## 5. Download design

- The dataset is fetched from a **configured source location**: type + path (+ credentials reference).
- One interface, **one implementation per location type**, chosen by a factory. Adding a type adds one class and one factory entry.
- Airflow ships provider packages for S3, GCS, Azure Blob and Google Drive, which is the natural way to read them. Check which are already in the official image.
- **Open:** where the location and credentials are stored (database, config file, Airflow connection). Never in the repo.
- **Open:** whether the Airflow job reuses the Middleware's Python code or carries its own download code.
- **Open:** whether plain HTTP(S) is a location type (the CFPB file itself is a plain URL).
- **Open:** where the file lands between download and ingest (local folder locally, object storage in the cloud).
- Facts that shape it: the CFPB filtered export is capped at 100,000 rows, the 3-month window is 2,036,290 rows, so the **3 months dataset is derived from the All file by filtering on `Date received`**. The file is about 350 MB zipped, and is not date-sorted in the sampled part, so the whole file is read. The API is not suitable for bulk (10,000-row window per query).

## 6. Ingest design

- A second DAG reads the downloaded data and writes MongoDB in **batches**.
- Idempotent: **upsert keyed by Complaint ID**, with a unique index, so retries and partial failures are safe.
- Start with plain Python (chunked read, bulk upserts). **PySpark** adds a JVM to the Airflow image and is likely unnecessary for 2M rows; decide after measuring the All dataset.
- Airflow can run batches in parallel (split by month or file chunk) without Spark; a single local Mongo node will not gain much from heavy parallelism.
- MongoDB needs its own approach for collections and indexes (Alembic does not cover it).

## 7. Migrations (Alembic)

- Alembic files live inside `Middleware/ConsumerComplaintsHandsOn` (`alembic.ini`, `alembic/`), outside the application layers.
- The database comes from the app settings (`CCA_DB_URL`, `CCA_DATA_DIR`), not `alembic.ini`, so the API and the migrations use the same database. `alembic/env.py` creates the three schemas first (`CREATE SCHEMA IF NOT EXISTS`; on SQLite the attached files).
- The `alembic_version` table sits in the main SQLite file `operational.sqlite`.
- Local start script (**implemented**, `run_app.sh start|stop|status`, `npm run local:handson:middlware:all:start|stop|status`): migrate, then start the API in the background; if the migration fails the API does not start.
- Never edit a migration once merged; add a new one (this narrows the missing-checksum gap).
- SQLite has limited `ALTER TABLE` (Alembic "batch mode" needed); test migrations against Postgres too.
- Alembic creates tables, not the database server or the empty database.
- Cloud: deferred to M03 (D34, D38).

## 8. Other open items

- Do the portal's accordions poll while something runs, or refresh on a button? **Open**
- Does Intellect share the operational database? **Open**
- What the portal's "Airflow" entry is (link to the Airflow UI, or its own screen). **Open**
- Return-code values: **Decided (D22)**, more may be added.
- Which schema holds `system_datasets` (planned: `consumer_comp_db`, next to `data_ingest_log`). **Proposed**
- The schema names mix `comp` and `compl` (`consumer_compl_intellect_db`); kept exactly as given. **Open** if it should be unified.
- User management and execution-log tables. **Open**
