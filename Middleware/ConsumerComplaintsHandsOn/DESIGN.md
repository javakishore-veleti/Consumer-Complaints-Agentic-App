# Design

Detailed decisions behind the [architecture](ARCHITECTURE.md). Features are in [PRODUCT_FEATURES.md](../../docs/PRODUCT_FEATURES.md).

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
| D11 | **SQLite is written only by the API.** Airflow reports progress by calling API endpoints. *(Reworded by D51: Airflow may read the database but never writes it.)* |
| D12 | The download is **asynchronous**: the facade triggers an Airflow DAG and returns. A separate DAG ingests into MongoDB. |
| D13 | DB Ingest is started **manually** from its own screen (left nav, parallel to Imports), not automatically after a download. |
| D14 | One common log table `data_ingest_log` with a `purpose` column, plus a `system_datasets` table with the current state. *(Superseded by D47.)* |
| D15 | **One endpoint starts any download**, taking a `usecase`. **One endpoint receives Airflow status updates**, taking `usecase` and `status`. *(Superseded by D46: there is no usecase; the endpoints take a workflow and an execution.)* |
| D16 | The dataset is **never committed to the repository**. *(The second sentence of this decision, "download reads from a configured location type and path", is superseded by D43: each workflow knows its own source, and the API has no source location types.)* |
| D17 | Locally the migrations run from the start script before the API starts; in the cloud they will run from a manually triggered workflow (M03, D34). |
| D18 | One OpenAPI (Swagger) specification for the whole hands-on project. |
| D19 | Local: 3 months dataset. Cloud: All dataset. Same code, different configuration. |
| D20 | MongoDB bulk ingestion by the Airflow job directly; PySpark only if measurements justify it. |
| D21 | Three schemas: **`consumer_comp_db`** (consumer complaints area: `data_ingest_log`, later `system_datasets`; also the MongoDB database name), **`consumer_compl_intellect_db`** (the Intellect app's own area), **`consumer_comp_users_db`** (user management). Names are exactly as given. On SQLite each schema is an attached database file named after it; on Postgres and similar they are real schemas. *(D48 adds the admin schema `consumer_comp_admin_db`.)* |
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
| D38 | **Milestones are scoped, and everything runs locally until the cloud milestone.** **M01** is the foundation: project organization (repository and conventions, Docker containers, the layered Middleware, the operational database with Alembic migrations, the API foundation) and the data ingest log API (create, get, list, update, delete). **M02** is downloads management: dataset status, the download API, the workflow registry (D43), the Airflow download DAGs and the admin portal. **M03** is cloud (AWS, Azure and GCP databases, the migration workflow, and the cloud workflows). The code keeps its seams (database URL in settings, one workflow engine class per engine type), so later milestones add code rather than rewrite it. | Finish a working, reviewable foundation first, then build on it milestone by milestone. |
| D39 | **A transaction that several DAO calls share is opened by a service, through the `TransactionDao`.** `begin` puts an opaque handle on a `TransactionCtx`; the service puts that on the ctx of each DAO call (every DAO ctx extends `TransactionalCtx`); the DAOs then join it and do not commit; the service commits, or rolls back when any step does not return SUCCESS. With no transaction on the ctx a DAO call runs and commits on its own. | Business rules that touch two tables stay in the services layer, the DAOs stay one per table, and nothing above `dao/impl` sees SQLAlchemy. `tests/test_dataset_status_service.py` proves it: if the second write fails, the first is not kept. |
| D40 | **`system_datasets` has one row per dataset and stage; the dataset row follows the log row.** Usecases map to rows (`download_3_months`, `download_all`, `ingest_3_months`, `ingest_all`). Requesting a run writes a `requested` log row and sets the row to `running`; a second request while it is running is a CONFLICT. A report (`started`, `completed`, `failed`) changes the newest log row of the usecase (D30 rules) and the dataset row together; the same report twice is accepted; a report carrying a `run_id` that differs from the newest row's `run_id` is a CONFLICT (an older run must not change the newest one). | Airflow retries callbacks and can be late, and the portal must always show one consistent state. *(Superseded by D47.)* |
| D41 | **The `system_datasets` table, its DAO and the dataset status service (D39, D40) belong to M02.** They were built early, while M01 was still being scoped; they stay in the code and their issues are closed under M02. | Keeps the milestone boards honest about what each milestone is for. *(Superseded by D47: the table is retired.)* |
| D42 | **The source location and credentials live in `.env`, and an API endpoint copies them into Airflow Variables.** *(Revised by D43: a workflow's non-secret settings now belong in its `config` JSON, so this decision covers credentials and any other secret. **Proposed**, to confirm.)* (1) Values are only in the git-ignored `.env`; a committed `.env.example` lists the names with empty values. (2) `CICD/Local/airflow/Airflow_Variables_Upsert.txt` lists, one per line, the Airflow Variable names to copy: names only, never values; blank lines and `#` comments are ignored. (3) `POST /management/airflow/upsert-secrets` (no body) reads each listed name's value from `.env` and creates or updates the Airflow Variable through Airflow's REST API. It returns one result per name (created, updated or missing) and never a value. A name missing from `.env` is reported and the rest still run, but the return code is a failure. The endpoint is protected by the shared secret of the callback endpoints. (4) DAGs read the location with `Variable.get`; credential names contain a word such as `secret` or `password` so Airflow masks them. (5) The Airflow username and password the endpoint uses also come from `.env`. (6) Airflow Connections for cloud credentials are deferred to M03 (D34, D38) and reuse this mechanism. (7) The endpoint is its own story under the Airflow download DAG feature, built before the DAG that reads the Variables. | Airflow never writes the database (D11) and the repo never holds a real value (D16); one `.env` serves the API and Airflow, the same code runs locally and in the cloud with different values (D19), and the committed list shows exactly which names reach Airflow. |
| D43 | **Workflows are registered in the database, and there is no source-location interface.** (1) Every workflow that downloads or ingests data is one row of **`app_workflows`** in the admin schema: `workflow_name` (up to 100 characters), the **workflow engine type** (Apache Airflow, AWS Step Functions or another engine), the **engine's own id** for the workflow (the Airflow DAG id, the Step Functions state machine) and a **JSON config** for anything about the workflow, so a definition is reusable. (2) Every execution is recorded in **`app_workflows_exec_log`** with the same information. (3) There may be several download workflows and each knows its own source, so the FastAPI app has no source location types and no `SourceLocation` interface or package (supersedes the second sentence of D16; M02 feature #46 and stories #47 to #50 are closed as not planned; the new work is feature #78 and its stories, and the open questions were settled in story #79, D46 to D53). (4) The portal lists the workflows from `app_workflows`; the FastAPI app starts the chosen one in its engine **asynchronously**; the engine calls the API when the run is complete (D11, D30); the portal reads the status through the API from whichever database is configured (SQLite, Postgres or MongoDB, behind the DAO interface). | The app stays agnostic of sources and engines; a new DAG or a new engine is data (and one engine class), not a code change in every layer. |
| D44 | **The Airflow DAGs live in `Middleware/Airflow-dags`, outside the FastAPI app root.** `Middleware/ConsumerComplaintsHandsOn` is always the FastAPI app root; the DAGs are not part of that app. The Airflow compose file mounts `Airflow-dags` by relative path as the DAGs folder, so a new or edited DAG is picked up without stopping or recreating the container (the refresh interval is set short for local use). The folder replaces the repository-root `dags/`. **Not built yet.** | DAGs and the API are separate deployables with separate lifecycles. |
| D45 | **Object factories are bean registries with an `init()`.** Like Spring bean ids: one interface, one or more implementations. Every `objects_factory` has an `init()` that the application's `main` calls once at startup (and that is safe to call twice); it creates each implementation as a singleton and registers it under its interface. Lookup is deterministic: where an interface has exactly one implementation the caller gets that instance (and it is an error if there are none or more than one); where the caller knows there are several, it gets the list of instances, in a fixed order. Each story that adds classes extends its package's factory to register them as singletons (a line in that story's acceptance). **Not built yet.** First candidate: looking up the workflow engine for an engine type (Proposed). | Refines D4, D25 and D26 (the factories exist today as lazy static methods without `init()`); nothing is retrofitted in one go, each package gains `init()` as stories touch it. |
| D46 | **There is no usecase; the workflow is the unit.** The portal lists workflows; the start endpoint takes a workflow; the engine's callback reports against an execution of a workflow; what the portal shows for a MIO comes from the logs below. | Supersedes D15 and D40. Everything the app starts, tracks and shows is a workflow or a run of one. |
| D47 | **`system_datasets` and `data_ingest_log` are retired.** Their role is taken by the catalog and the logs of D49 and D50. The code and tables stay until a removal story drops them (DAOs, `DatasetStatusService`, `/data-ingest-logs`, the two Alembic migrations stay as history and a new migration drops the tables). | The portal's "3 months" and "All" accordions become MIOs (D49). Supersedes D14, D40 and D41. |
| D48 | **`consumer_comp_admin_db` is the schema for everything admin-related**: the workflow registry (D43) and the catalog (D49). `consumer_comp_db` stays as the name of the MongoDB database that holds the complaint data. | Adds a fourth schema to D21. The admin portal manages every table in it. |
| D49 | **The catalog is data, in tables.** **`datasets`**: the master list (name, description). **`datasets_location`**: where a dataset is available; one dataset has several rows (S3, local, FTP, Google Drive, GitHub, plain HTTP(S) and so on): a location type code, a path, and a credentials reference (the name of a secret, never a value). **`mios`**: managed information objects, predefined and seeded by hand for now (customer complaints 3, 6, 9 and 12 months, 2026 and so on). **`mios_datasets`**: attaches datasets, and the chosen location of each, to a MIO. Location types are values in `datasets_location`, not code: there is no source-location interface (D43). | The data about where a dataset lives is managed in the admin portal and read by the workflows. |
| D50 | **Two logs, with different jobs.** **`app_workflows_exec_log`** is global: every execution of every workflow. **`mios_ingest_log`** is specific to a MIO: what was ingested, its status, and its volume. One MIO ingest can involve **many executions** (reruns after failures, batches, a large dataset split into parts), so an exec-log row carries an optional reference to a `mios_ingest_log` row; a workflow without a MIO (a RAG workflow later) leaves it empty. Status changes of both follow the D30 rules. | The same execution record serves every workflow, while the MIO view stays about the MIO. |
| D51 | **A workflow works out its own configuration.** The API creates the execution row and starts the workflow with only that row's id; the DAG reads the tables itself (workflow, MIO, dataset location, config) from whichever database is configured (SQLite, Postgres or MongoDB). **Airflow may read the operational database but never writes it** (it reports progress by calling the API, D11). The database URL reaches Airflow as an Airflow Variable (D42); the driver must be in the Airflow image (Postgres and SQLAlchemy are; MongoDB needs `pymongo`). Advanced configuration is a later step. | Simple for now. **Open risk:** a container reading the local SQLite file through a Docker bind mount can hit locking or file-sharing problems; if so, run the operational database on Postgres locally (D9 allows the swap). |
| D52 | **`engine_type` is a short code, validated against the engine classes registered at startup (D45).** Values: `apache_airflow` now, `aws_step_functions` when its class exists. **M02 supports Apache Airflow only**; Step Functions comes with the cloud work (M03). Proposed columns of `app_workflows`: id, `workflow_name` (up to 100 characters, unique), `engine_type`, `engine_workflow_id`, `config` (JSON), `enabled`, created and updated times. | Adding an engine is one class and no migration. |
| D53 | **The RAG layer is a later milestone, recorded here as direction only.** **`mios_rags`** describes the RAG technology stack of a MIO (Milvus, Postgres, Chroma, AWS OpenSearch and others, on local, AWS, Azure or GCP); one MIO can have several stacks so performance and cost can be compared. RAG workflows are their own entries in `app_workflows`, separate from the ingest workflows; they take the ingested data and run in **batch or incrementally**, chosen by volume. | No M02 stories. A new milestone will cover it. |
| D54 | **MVP first.** M02 builds the smallest flow that runs end to end (start a workflow from the portal, Airflow downloads, the status comes back) and accepts refactoring afterwards. After the MVP: the factory `init()` of D45, the engine interface, the list-workflows endpoint, the 3-month filter and the removal of the retired tables. | Working software sooner; the design above stays the direction, and refactoring later is accepted. |
| D55 | **Naming and types.** In class names `Workflows` is shortened to `Wf` (`AppWfDao`, `AppWfCtx`); table names stay in full (`app_workflows`), module names follow the class names. Every type list of the app (engine types, later location types and statuses) is an enum in `app/core/common/app_types_constants.py`, all with the parent `AppTypeEnum`. A JSON column that holds nothing is NULL, not `{}`. | Short class names stay readable; one file lists every allowed value. Refines D52: the DAO checks `engine_type` against `EngineType`, the registered engine classes are checked later (#83, #42). |

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

### `data_ingest_log` (append-only history) — Implemented (schema `consumer_comp_db`, migration `0001`); **retired by D47, removal is its own story**
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
| (optional) source type / path | where the data came from (**Open:** likely dropped, see D43 and `app_workflows_exec_log`) |

### `system_datasets` (current state) — Implemented (schema `consumer_comp_db`, migration `0002`); **retired by D47, removal is its own story**
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

### The admin schema `consumer_comp_admin_db` (D48) — **Decided (D43, D46 to D52), not built**
All tables below live in it. Column lists marked *(Proposed)* are defaults that can change.

#### `app_workflows` (the registry of workflows)
One row per workflow the portal can list and start.

| Column | Meaning |
|---|---|
| id | application-generated ID |
| workflow_name | up to 100 characters, unique *(Proposed)*, what the portal shows |
| engine_type | short code of the engine: `apache_airflow`, later `aws_step_functions` (D52) |
| engine_workflow_id | the engine's own id for it: the Airflow DAG id, the Step Functions state machine |
| config | JSON: anything about the workflow; non-secret values only, secrets stay in `.env` and Airflow Variables (D42) |
| enabled, created_at, updated_at | *(Proposed)* |

#### `app_workflows_exec_log` (every execution of every workflow, D50)
| Column | Meaning |
|---|---|
| id | application-generated ID; the only value the API hands to the engine (D51) |
| workflow | the `app_workflows` row |
| workflow_name, engine_type, engine_workflow_id | copied from the registry row at execution time |
| mios_ingest_log | optional: the MIO ingest this execution belongs to (many executions to one ingest) |
| config used, engine run id | *(Proposed)* the JSON in force, and the engine's run id (for example the Airflow run id) |
| status, message, requested / started / finished times | *(Proposed)* statuses requested, started, completed, failed; D30 rules |

#### The catalog (D49)
| Table | Columns *(Proposed)* |
|---|---|
| `datasets` | id, name (unique), description |
| `datasets_location` | id, dataset, location type (code), path, credentials reference (a name, never a value), description |
| `mios` | id, name (unique), description |
| `mios_datasets` | id, mio, dataset, dataset location (the chosen one) |
| `mios_ingest_log` | id, mio, status (D30 rules), message, requested / started / finished times, volume (rows loaded, batch or increment markers) |

- **Open:** how the status of a `mios_ingest_log` row is derived from its executions (for example completed only when every execution is completed, failed when one fails and is not rerun), and the exact volume columns.
- **Open:** the list of location type codes (for example `local`, `http`, `github`, `s3`, `azure_blob`, `gcs`, `google_drive`, `ftp`); the DAGs interpret them, the API does not (D43).
- **Open:** how a workflow is attached to a MIO (reusable across MIOs, or specific to one), for example a link table or a value in the workflow's config.
- Seeding: the predefined MIOs and their datasets and locations are inserted by migration or script for now; managing them from the portal is later.

Users are a further table, to be defined.

## 4. API contract (Proposed; one OpenAPI spec)

### 4.1 Workflows
There is no usecase (D46). The unit is a registered workflow (`app_workflows`); a run of it is a row of `app_workflows_exec_log`.

### 4.2 Endpoints
| Purpose | Called by | Input |
|---|---|---|
| List workflows | admin portal | none |
| Start a workflow | admin portal | the workflow; optionally the MIO and the dataset location. Creates the execution row, starts the run in its engine, returns at once with the execution id |
| Status update (engine callback) | Airflow | the execution id, `status` (started, completed, failed), optional engine run id and `message` |
| Read status | admin portal | none or a MIO (what the accordions show: the MIOs and the status of their ingests and executions) |

- The callback endpoints need a **shared secret**; the caller is Airflow, not a person.
- Allowed status changes: requested -> started -> completed or failed (D30). Anything else (duplicate, out of order) is ignored or rejected, because Airflow retries.
- **Open:** one "completed" endpoint with an outcome, or separate completed and failed endpoints. **Open:** code-first (FastAPI generates the spec, exported to a committed file) versus spec-first, and where the file lives. Leaning: code-first with an exported file.
- The DAG's final task must run even when earlier tasks fail, so a crashed run does not leave the execution stuck on "running".

## 5. Download design

- **Decided (D43):** downloads are **workflows**, registered in `app_workflows`. There can be several download workflows, and each knows its own source. The portal lists them; the FastAPI app starts the chosen one in its engine asynchronously; the engine reports completion by calling the API; the portal reads the status through the API.
- **Decided (D43):** the API has **no source-location interface and no source location types**. Anything about where the data comes from belongs to the workflow (its code and its JSON config), not to the app. Features #46 to #50 of M02 are superseded by this.
- **Decided (D44):** the Airflow DAGs live in `Middleware/Airflow-dags`, outside the FastAPI app root, mounted into Airflow by relative path so new DAGs appear without a restart.
- **Decided (D42, revised by D43):** credentials stay in `.env` and reach Airflow as Variables through `POST /management/airflow/upsert-secrets`. Non-secret settings: where a dataset lives is in `datasets_location` (D49), anything else about the workflow is in its `config` JSON.
- Airflow ships provider packages for S3, GCS, Azure Blob and Google Drive; a DAG that reads one of those uses them. Check which are already in the official image.
- **Decided (D51):** the workflow works out its own configuration by reading the tables; the API passes only the execution id. Where the DAG finds the database URL: an Airflow Variable.
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
- The schema names mix `comp` and `compl` (`consumer_compl_intellect_db`); kept exactly as given. **Open** if it should be unified.
- User management tables. **Open**
- The admin schema is `consumer_comp_admin_db`. **Decided (D48)**
- `system_datasets` and `data_ingest_log` are retired and replaced by the catalog and the two logs; there is no usecase. **Decided (D46, D47, D49, D50)**
- How a workflow reads its configuration. **Decided (D51)** (open risk: SQLite through a Docker bind mount)
- Engine types and the first engine: `apache_airflow` only in M02. **Decided (D52)**. Whether the API starts a run through a `WorkflowEngine` interface in `services/`, one implementation per engine type, looked up through the factory (D45). **Proposed**
- The RAG layer (`mios_rags`, RAG workflows, batch or incremental runs) is a later milestone. **Decided (D53)**
- M02's feature #46 and stories #47 to #50 are closed as not planned; feature #78 (Workflow registry) and its stories replace them. **Decided**
- The open items listed in section 3 (ingest status derivation, location type codes, attaching workflows to MIOs). **Open**
