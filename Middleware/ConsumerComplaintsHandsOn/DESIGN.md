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
| D17 | Locally the migrations run from the start script before the API starts; in the cloud a manually triggered GitHub Actions workflow runs them. |
| D18 | One OpenAPI (Swagger) specification for the whole hands-on project. |
| D19 | Local: 3 months dataset. Cloud: All dataset. Same code, different configuration. |
| D20 | MongoDB bulk ingestion by the Airflow job directly; PySpark only if measurements justify it. |

## 2. Conventions in detail

### 2.1 Ctx, Req, Resp
- `XxxReq`: what the caller sends. `XxxResp`: what comes back. `XxxCtx`: holds both.
- Results are written into `ctx.resp`; the integer return is only the outcome code (success, failure, or another code defined later).
- **Proposed:** the ctx also has a working area for values passed between tasks (for example the log row ID task 1 creates and task 3 needs), so `resp` holds only what the caller receives. **Open.**
- **Open:** which ctx does a DAO receive? If tasks pass the facade's ctx down, a lower layer depends on an upper layer. Two ways out: put every Req/Resp/Ctx type in `common/dtos`, or give each DAO its own small ctx that the task fills in. Leaning: the second.

### 2.2 Interfaces and factories
- Import rule: you may import a package's interface and its `objects_factory`; you may never import its `impl/`.
- A factory picks the implementation from configuration. **Open:** one cached instance (singleton) or a new object per call; whether factory functions are exempt from the "always take ctx" rule. Leaning: cache DAOs that hold a database engine.
- **Proposed:** a tool such as `import-linter` can enforce the layer rules in the build.

### 2.3 Facade tasks
- The facade's factory builds the ordered task list; the facade runs them in order.
- **Open:** on a non-success return, does the facade stop or continue? Leaning: stop at the first failure.

### 2.4 ORM and transactions
- SQLAlchemy table classes stay inside `dao/impl/`. DAOs convert them to and from plain Req/Resp objects.
- Updating `data_ingest_log` and `system_datasets` together must be **one transaction**. **Open:** a small service that owns "record the outcome" and calls both DAOs in one transaction, or a transaction handle passed through the ctx. Leaning: the service (it is business logic and services are the open layer).
- Use application-generated IDs (UUID strings) and UTC timestamps, so nothing is tied to one database.

## 3. Operational data model (SQLite)

### `data_ingest_log` (append-only history) — Proposed
| Column | Meaning |
|---|---|
| id | application-generated ID |
| purpose | the usecase, a fixed set (see 4.1) |
| status | requested, started, completed, failed |
| run_id | Airflow run ID, used to match callbacks |
| message | error text on failure |
| requested_at, started_at, finished_at | UTC timestamps |
| (optional) source type / path | where the data came from |

### `system_datasets` (current state) — Proposed
**Open:** one row per dataset and stage, JSON, or independent columns.
- Row per dataset and stage is proposed: adding a dataset or stage is just new rows, no migration, no JSON read-modify-write race between two callbacks.

| dataset | stage | status | last log row | updated |
|---|---|---|---|---|
| 3_months | download | not_started / running / completed / failed | log id | UTC time |
| 3_months | db_ingest | ... | ... | ... |
| all | download | ... | ... | ... |
| all | db_ingest | ... | ... | ... |

- A `usecase` maps to exactly one row (dataset + stage), and is the value of the log's `purpose`.
- Status is a value, not a boolean: the UI must tell not started, running, completed and failed apart.
- **Open:** a new download of the 3-month dataset resets its ingest status (leaning yes). **Open:** record the absolute date range covered.

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

- Alembic files live inside `Middleware/ConsumerComplaintsHandsOn`, outside the application layers.
- Local start script: migrate, then start the API.
- Never edit a migration once merged; add a new one (this narrows the missing-checksum gap).
- SQLite has limited `ALTER TABLE` (Alembic "batch mode" needed); test migrations against Postgres too.
- Alembic creates tables, not the database server or the empty database.
- Cloud: manual GitHub Actions workflow; credentials as environment secrets. **Open:** how the runner reaches a private database.

## 8. Other open items

- Do the portal's accordions poll while something runs, or refresh on a button? **Open**
- Does Intellect share the operational database? **Open**
- What the portal's "Airflow" entry is (link to the Airflow UI, or its own screen). **Open**
- Return-code values. **Open** (defined later)
- User management and execution-log tables. **Open**
