# Consumer-Complaints-Agentic-App

## Introduction

**Consumer Complaints Agentic App (CCAA)** is a hands-on platform to bring the public [CFPB Consumer Complaint Database](https://www.consumerfinance.gov/data-research/consumer-complaints/) into your own environment through an **Admin portal**, and to grow toward an **Intellect** layer (search, RAG, agentic analysis) on that data.

Operators do not push millions of rows through a browser. They work in **Managed Information Objects (MIOs)**—for example “all complaints” or “last 3 months”—start the right **registered workflow**, and watch status return through the API. Heavy lifting (download the All zip, derive a date window, later batch ingest into MongoDB) runs **asynchronously** in Apache Airflow. The complaint dataset is **never committed** to this repository.

**Vision:** a reliable local-to-cloud path for complaint data ops first; then intelligence products that reason over the same MongoDB corpus. Milestones already prove Admin → API → Airflow → callback → UI refresh with a pluggable operational store (SQLite by default; Postgres or Mongo via `.env`).

Product intent: [`docs/PRODUCT_FEATURES.md`](docs/PRODUCT_FEATURES.md). Detailed rules: [`Middleware/ConsumerComplaintsHandsOn/DESIGN.md`](Middleware/ConsumerComplaintsHandsOn/DESIGN.md).

## Overall architecture

Capability view (not a folder map):

1. **Experience** — Angular Admin portal: Imports, per-MIO status, start only *allowed* workflows for that MIO.
2. **Integration** — FastAPI Middleware: workflow registry, start execution, MIO status, Airflow status callbacks (shared secret). Sole writer of the **operational/admin** catalog and logs.
3. **Orchestration** — Apache Airflow: download CFPB All, filter a 3-month slice, future DB ingest DAG. Reports `started` / `completed` / `failed` back to the API.
4. **Data** — Operational store (SQLite / Postgres / Mongo) for workflows, MIOs, bindings, ingest/exec logs; separate **complaint documents** MongoDB written only by the ingest job.
5. **Source** — CFPB public HTTP export (All zip). Filtered site downloads cannot cover multi-million-row windows, so 3 months is derived from All.
6. **Future** — `consumer-complaints-Intellect` reads complaint MongoDB for RAG / agentic workflows.

Write rules that never bend: **API owns operational data**; **Airflow owns bulk complaint MongoDB** (and may *read* operational config, never write it).

![CCAA enterprise architecture](docs/Design/ccaa-enterprise-architecture.jpg)

Layered Middleware internals (closed API → facades → open services → DAO) and deeper diagrams: [`ARCHITECTURE.md`](Middleware/ConsumerComplaintsHandsOn/ARCHITECTURE.md).

> [!CAUTION]
> # Install Superpowers on your laptop
> **To truly use this repo’s Superpowers integration (structured agent workflows: brainstorm → plan → TDD → review), each developer must install the [Superpowers](https://github.com/obra/superpowers) plugin in Cursor on their machine.**
>
> In Cursor, run:
> ```text
> /add-plugin superpowers
> ```
> Workspace setting `.cursor/settings.json` only *enables* the plugin for this project — it does **not** ship the skills in git.
>
> **The application still runs without Superpowers.** Middleware, Admin portal, Airflow, migrations, and tests work with the npm/local scripts below. Superpowers is for AI-assisted *development process*, not runtime.

## Development tooling

### Local containers (lite profiles)

Default local path uses **SQLite** for the operational/admin store — **no operational Postgres container**. Start Airflow only:

```bash
npm run local:containers:sqlite:start    # Airflow (SQLite-lite default)
npm run local:containers:sqlite:status   # shows expected: airflow
```

Opt-in profiles:

```bash
npm run local:containers:postgres:start  # Airflow + CCA operational Postgres
npm run local:containers:mongodb:start   # Airflow + MongoDB
```

`npm run local:containers:all:*` still starts/stops/status **every** `CICD/Local/*/docker-compose.yaml`. **Stop always removes Docker volumes** (`docker compose down -v`) so Airflow/Mongo/Postgres data does not linger (M01-0073 / #133). Pass `--keep-volumes` to `CICD/Local/docker-all-down.sh` only when you intentionally want to keep them. For Postgres/Mongo app config, set `.env` per `Middleware/ConsumerComplaintsHandsOn/.env.example` (D75–D78).

### Recommended local stack (three steps)

```bash
npm run local:containers:all:start          # or :sqlite:start / :postgres:start / :mongodb:start
npm run local:handson:middlware:all:start   # Middleware API (:8000)
npm run local:portals:all:start             # all Portals apps (today: admin on :4200)
```

`local:portals:all:*` is the umbrella for every app under `Portals/`; add future portals there. `local:portals:all:start` always runs `npm install` in the admin portal first (so pulls never leave deps stale), then `ng serve`. Single-app shortcuts remain: `local:portal:admin:start|build|test`. Shortcut `local:portal:admin:with-api` still starts Middleware then `local:portals:all:start`.

Admin Angular needs **Node.js 22+** (see root `.nvmrc`). If `nvm` defaults to 20:

```bash
nvm use    # or: nvm use 22
npm run local:portals:all:start
```

Then open http://localhost:4200/datasets/imports.

E2E happy path (UI → API → Airflow → callback → UI, SQLite first): see `docs/local-admin-e2e-happy-path.md`. CI smoke: `npm run local:e2e:happy-path:smoke`. Live API probe: `npm run local:e2e:happy-path:probe`. DoD matrix (SQLite / Postgres / MongoDB): `docs/local-admin-e2e-dod-matrix.md` · `npm run local:e2e:dod-matrix:smoke`.

### Local URLs, usernames, and passwords

Defaults from `CICD/Local/*/docker-compose.yaml` and portal/API scripts. **Local-only** — never reuse these in cloud. Copy `Middleware/ConsumerComplaintsHandsOn/.env.example` → `.env` (git-ignored) and fill from this table.

#### Host apps (not Docker)

| Service | URL | Username | Password | Notes |
|---|---|---|---|---|
| Middleware API | http://127.0.0.1:8000 | — | — | `npm run local:handson:middlware:all:start`; OpenAPI at `/docs` |
| Admin portal | http://127.0.0.1:4200 | — | — | Proxies `/api` → API `:8000` |
| Intellect portal | http://127.0.0.1:4201 | — | — | Proxies `/api` → API `:8000` |
| SQLite operational DB | `Middleware/ConsumerComplaintsHandsOn/.data/operational.sqlite` | — | — | Default when `CCA_OPERATIONAL_STORE` / `CCA_DB_URL` unset |

#### Containers

| Service | URL / connection | Username | Password | `.env` / notes |
|---|---|---|---|---|
| Airflow UI + API | http://127.0.0.1:8080 | `airflow` | `airflow` | `CCA_AIRFLOW_API_BASE_URL`, `CCA_AIRFLOW_API_USERNAME`, `CCA_AIRFLOW_API_PASSWORD` |
| Airflow metadata Postgres | (internal Docker only) | `airflow` | `airflow` | DB `airflow`; not the CCA operational store |
| CCA ops Postgres (+ pgvector) | `postgresql://postgres:postgres@127.0.0.1:5432/cca` | `postgres` | `postgres` | DB `cca`. Set `CCA_OPERATIONAL_STORE=postgres`, `CCA_DB_URL=postgresql+psycopg://postgres:postgres@127.0.0.1:5432/cca`, `CCA_PGVECTOR_URL=postgresql://postgres:postgres@127.0.0.1:5432/cca` |
| MongoDB | `mongodb://root:changeme-local@127.0.0.1:27017/?authSource=admin` | `root` | `changeme-local` | Complaints: `CCA_MONGO_COMPLAINTS_URL=…/consumer_comp_db?authSource=admin`. Ops profile: `CCA_OPERATIONAL_STORE=mongodb`, `CCA_MONGO_OPERATIONAL_URL=…/cca_operational?authSource=admin` |
| Chroma | http://127.0.0.1:8000 (compose default) | — | — | `CCA_CHROMA_URL`. **Conflicts with Middleware `:8000`** — prefer `CCA_CHROMA_PORT=8100` and `CCA_CHROMA_URL=http://127.0.0.1:8100` |
| Redis Stack | `redis://127.0.0.1:6379/0` | — | — | `CCA_REDIS_URL`. RedisInsight UI: http://127.0.0.1:8001 |

#### Required Middleware `.env` for live Airflow callbacks

| Variable | Example local value | Purpose |
|---|---|---|
| `CCA_CALLBACK_SECRET` | `openssl rand -hex 32` | Shared secret; Airflow callbacks send `X-Callback-Secret` (401 without it) |
| `CCA_API_URL` | `http://host.docker.internal:8000` | Base URL workers use to reach Middleware (Docker Desktop) |
| `CCA_AIRFLOW_API_PASSWORD` | `airflow` | Matches Airflow WWW user (with username `airflow`) |
| `CCA_VECTOR_STORE_PATH` | e.g. absolute path under Airflow data | JSONL vector index (`index_cfpb_all`) |
| `LOCAL_DATA_PATH_CFPB` | e.g. `/opt/airflow/data/cfpb` | Where CFPB zips land inside the Airflow worker |
| `CCA_CFPB_SPLIT_SOURCE_PATH` | machine-local path to `complaints_part_*.csv.zip` | Optional split-parts staging (D91) |

After containers + `.env`: `npm run local:api:migrate` (SQLite/Postgres), sync Airflow Variables from Admin **Operations → Sync secrets**, then open Admin Imports.

### Superpowers plugin

> [!IMPORTANT]
> Superpowers is **required for the agent workflow** documented here, but **optional for running the product**. See the red **CAUTION** banner just above Development tooling.

This project uses the [Superpowers](https://github.com/obra/superpowers) plugin in Cursor (install on **your laptop**, not vendored into this repo). It is a core skills library that gives the AI agent structured workflows for development tasks.

Skills included:

- **Planning and design:** `brainstorming`, `writing-plans`, `executing-plans`
- **Building and testing:** `test-driven-development`, `subagent-driven-development`, `dispatching-parallel-agents`, `using-git-worktrees`
- **Debugging and quality:** `systematic-debugging`, `verification-before-completion`
- **Code review and wrap-up:** `requesting-code-review`, `receiving-code-review`, `finishing-a-development-branch`
- **Meta:** `using-superpowers`, `writing-skills`

A `sessionStart` hook loads the `using-superpowers` skill at the start of each session, so the agent checks for a relevant skill before it acts.

To install it in Cursor, run:

```
/add-plugin superpowers
```

Invoke a skill directly with `/`, for example `/brainstorming`. The agent also uses skills automatically when they apply.

#### The basic workflow

See [The Basic Workflow](https://github.com/obra/superpowers#the-basic-workflow) in the Superpowers README. In short:

1. **brainstorming:** Runs before building anything. It draws out what you want and why, then plays its understanding back for correction.
2. **using-git-worktrees:** Runs after design approval. It creates an isolated workspace on a new branch and verifies a clean test baseline.
3. **writing-plans:** Breaks the approved design into small tasks (2-5 minutes each), with exact file paths and verification steps.
4. **subagent-driven-development** or **executing-plans:** Runs the plan, either with a fresh subagent and review per task, or inline with one review of the whole branch at the end.
5. **test-driven-development:** Enforces RED-GREEN-REFACTOR during implementation.
6. **requesting-code-review:** Reviews work against the plan between tasks and reports issues by severity.
7. **finishing-a-development-branch:** Verifies tests and presents merge, PR, keep or discard options.

The agent checks for relevant skills before any task, so these workflows are mandatory rather than optional.
