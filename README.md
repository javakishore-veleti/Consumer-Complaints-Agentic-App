# Consumer-Complaints-Agentic-App

## Introduction

**Consumer Complaints Agentic App (CCAA)** is a hands-on platform to bring the public [CFPB Consumer Complaint Database](https://www.consumerfinance.gov/data-research/consumer-complaints/) into your own environment through an **Admin portal**, and to grow toward an **Intellect** layer (search, RAG, agentic analysis) on that data.

Operators do not push millions of rows through a browser. They work in **Managed Information Objects (MIOs)**—for example “all complaints” or “last 3 months”—start the right **registered workflow**, and watch status return through the API. Heavy lifting (download the All zip, derive a date window, later batch ingest into MongoDB) runs **asynchronously** in Apache Airflow. The complaint dataset is **never committed** to this repository.

**Vision:** a reliable local-to-cloud path for complaint data ops first; then intelligence products that reason over the same MongoDB corpus. Milestones already prove Admin → API → Airflow → callback → UI refresh with a pluggable operational store (SQLite by default; Postgres or Mongo via `.env`).

Product intent: [`docs/PRODUCT_FEATURES.md`](docs/PRODUCT_FEATURES.md). Detailed rules: [`Middleware/ConsumerComplaintsHandsOn/DESIGN.md`](Middleware/ConsumerComplaintsHandsOn/DESIGN.md).

### Consumer finance

Consumer finance covers how individuals and households manage, borrow, save, invest, and protect their money.

- **Cash flow & budgeting** — income vs expenses; a budget that funds needs, wants, and savings; an emergency reserve for unexpected costs
- **Credit & debt** — credit scores, APR, principal vs interest, and debt-to-income when borrowing
- **Saving & investing** — compounding, inflation and purchasing power, diversification, tax-advantaged accounts
- **Risk protection & consumer rights** — insurance and deductibles; rules enforced by agencies such as the [CFPB](https://www.consumerfinance.gov/) (for example disputing credit-report errors and clear loan disclosures)

This app operates on **CFPB consumer complaint** records inside that domain.

### Understanding of Consumer Financial Data

Localhost work often uses a **three-month** window from the public [CFPB Consumer Complaint Database](https://www.consumerfinance.gov/data-research/consumer-complaints/) (for example a recent `date_received` range derived from the All export). Records are anonymized complaints the CFPB **sent to companies** for a response.

**Column groups** (CFPB field reference):

| Group | Fields |
|---|---|
| Tracking & dates | `Complaint ID`, `Date received`, `Date sent to company`, `Submitted via` |
| Product & issue | `Product`, `Sub-product`, `Issue`, `Sub-issue` |
| Company & resolution | `Company`, `Company response to consumer`, `Company public response`, `Timely response?` |
| Demographics & location | `State`, `ZIP code`, `Tags` (e.g. Older American, Servicemember) |

**Context for recent windows (from ~August 2026 onward):**

- **No free-text narratives** in the live database for this period — `Consumer complaint narrative` is typically blank; retrieval leans on structured categories plus synthesized text for vectors
- Only complaints sent for a company response are published; complaints referred to other regulators (for example many smaller depository institutions) are excluded
- **Not a statistical sample** of all consumers’ experiences; company complaint volume should be read with company size / market share in mind
- One complaint is not representative of all consumers; the public database generally **updates daily**

**Illustrative record shape** (fictional values — not a real complaint):

```text
Complaint ID: 00000000
Date received / Date sent to company: 2026-09-01
Product / Sub-product: Checking or savings account / Checking account
Issue / Sub-issue: Managing an account / Funds not handled or disbursed as instructed
Company: Example Bank, N.A.
State / ZIP / Tags: XX / 00000 / Servicemember
Submitted via: Web
Company response to consumer: Closed with explanation
Timely response?: Yes
```

After Mongo ingest, `_id` and `Complaint ID` may both hold the same public tracking number; treat **`Complaint ID`** as the stable key for indexing and joins.

### Data Products Ideas

Even without narratives, **semantic search + metadata filters** support products such as:

1. **Compliance / risk copilot (RAG)** — plain-language questions grounded in complaint IDs and facets (product, state, tags, dates)
2. **Issue clustering & trend detection** — similar patterns across companies or regions before they escalate
3. **Peer resolution advisor** — how comparable sub-issues were closed (e.g. explanation vs monetary relief)
4. **Triage / routing assist** — map incoming tickets to historical Product / Issue / Sub-issue; surface priority tags

**Portability:** start with local Chroma (and other local backends already in this repo). The same document-summary + metadata schema can later target open-source stores (e.g. pgvector, Qdrant, Milvus, Weaviate) or cloud vector products on AWS, Azure, and GCP — see milestone **M90** for cloud deployment; this README lists product *ideas*, not those builds.

### Consumer Financial Data Embeddings Exploration

Recent CFPB windows often have **structured categories only** (little or no free-text narrative). Indexing that corpus in a vector store (Chroma first; other open-source and cloud stores later) works best when each row is split into a **document string for embeddings** and **strict metadata for exact filters**. The notes below capture the exploration of that design as a short Q&A.

#### What does “descriptive text summary paired with strict metadata filters” mean?

Split each complaint row into two inputs before upsert:

1. **Document (text summary)** — a string the embedding model turns into one vector for **semantic** similarity (“funds not sent” ≈ “funds not handled or disbursed”).
2. **Metadata** — flat key/value fields stored beside the vector for **exact** constraints (company, state, product, date ranges), like a `WHERE` clause.

Embeddings alone are weak at hard filters (“only this company”, “on or after this date”). Metadata alone cannot match paraphrases. Together they support hybrid queries: filter first (or jointly), then rank by vector similarity inside the reduced set.

#### How would an illustrative row split?

Using the **fictional** shape above (`Complaint ID: 00000000`, Example Bank), not a live export row:

**Document (compact key–value — preferred starting point):**

```text
Product: Checking or savings account - Checking account | Issue: Managing an account - Funds not handled or disbursed as instructed | Tag: Servicemember | Resolution: Closed with explanation
```

**Metadata (exact filters; dates as integers help range queries):**

```json
{
  "complaint_id": "00000000",
  "company": "Example Bank, N.A.",
  "state": "XX",
  "zip_code": "00000",
  "product": "Checking or savings account",
  "sub_product": "Checking account",
  "issue": "Managing an account",
  "sub_issue": "Funds not handled or disbursed as instructed",
  "tags": "Servicemember",
  "company_response": "Closed with explanation",
  "timely_response": true,
  "date_received_int": 20260901
}
```

**At query time (hybrid):** for a question like “checking money-transfer problems in state XX after 2026-08-20 for Example Bank”, apply metadata (`company`, `state`, `date_received_int >= 20260820`) and embed the free-text question against document strings so rows about “funds not handled…” can rank highly even when the user did not type the official Sub-issue wording.

#### Do fixed sentence prefixes like “Complaint regarding a…” help?

Often **no** for this corpus. CFPB Product / Issue / Sub-issue phrases are already rich. Repeating the same English boilerplate on every row:

- Pulls vectors toward a shared “generic complaint” region and **dilutes** differences between issues
- Does **not** grow the stored vector’s byte size (dimension is fixed), but it can raise token/latency cost when embedding

**Three document formats:**

| Approach | Example shape | When |
|---|---|---|
| Pure value concatenation | `Checking or savings account \| Checking account \| Managing an account \| …` | Max signal, min noise; keyword-ish queries |
| Compact key–value | `Product: … \| Issue: … \| Resolution: …` | Best default balance; labels keep roles (outcome vs issue) |
| Full natural sentences | “On … a Servicemember submitted …” | Only if queries are long conversational sentences and the model is tuned for asymmetric sentence retrieval |

**Practical pick for CFPB structured rows:** skip conversational fluff; use **pure concatenation** or **compact key–value**.

#### What do you mean by “asymmetric sentence retrieval”?

**Asymmetric retrieval** (or asymmetric semantic search) happens when the user’s search query and the stored database document are fundamentally different in length, structure, or phrasing—yet need to match based on meaning.

In a standard **symmetric** search, you compare two similar things (for example, matching a tweet to a similar tweet, or a news headline to another news headline). In **asymmetric** search, you are matching a short, natural question against a longer, differently structured record.

**How this applies to CFPB-shaped data**

This project is a textbook example of asymmetric retrieval because the two inputs look completely different:

- **The query** (short, conversational, symptom-based):  
  `Why are banks holding up military members' wire transfers?`
- **The stored document** (structured, categorical, label-based):  
  `Product: Checking or savings account - Checking account | Issue: Managing an account - Funds not handled or disbursed as instructed | Tag: Servicemember | Resolution: Closed with explanation`

Notice that the query and the document share almost zero exact words (“wire transfer” vs “Funds not handled or disbursed as instructed”, “military members” vs “Servicemember”), and one is a question while the other is a structured tag summary.

**Why some embedding models fail at asymmetric search**

- **Symmetric models** (e.g. older `all-MiniLM` setups): Trained on pairs of similar sentences (paraphrases). Because they expect both texts to look alike, they often penalize matches when one text is a conversational question and the other is a structured database record.
- **Asymmetric models** (e.g. E5, BGE, Cohere embed-v3): Trained on question-and-answer datasets (like MS MARCO) where short queries are paired with structured passages. They learn to map a question about a problem to the region in vector space where the description/answer to that problem lives.

**How asymmetric models handle this in practice**

Many asymmetric embedding models ask you to add special instruction prefixes so the model knows which role each text plays:

```python
# When indexing a CFPB-shaped row, mark it as a stored document:
doc_text = "passage: Product: Checking account | Issue: Funds not handled or disbursed as instructed"

# When a user searches, mark their input as a search query:
query_text = "query: bank failed to send my wire transfer"
```

By using `query:` and `passage:` prefixes (used by models like `intfloat/e5`), the model adjusts its math to bridge the gap between how humans ask questions and how the database stores structured facts.

#### How do you choose an embedding model here?

Criteria that matter for Chroma-now / multi-cloud-later:

1. **Portability** — vectors from model A cannot be queried by model B. Prefer open-weights or a cloud-agnostic API so you can embed once (e.g. store vectors with raw JSON in Parquet) and load the **same** vectors into Chroma, AWS, Azure, or GCP without re-embedding.
2. **Asymmetric retrieval** — short structured documents vs conversational user questions; models trained for query↔passage help.
3. **Dimension vs scale** — for a finite CFPB category vocabulary, **~384–1024** dims is usually enough; larger dims cost more storage/latency.
4. **Matryoshka / truncatable dims (MRL)** — some models let you shorten vectors with limited quality loss when cloud bills matter.

| Model family | Type | Dim (typical) | Fit |
|---|---|---|---|
| `BAAI/bge-base-en-v1.5` (or large) | Open weights | 768 / 1024 | Local Chroma, portable, no API cost |
| `intfloat/e5-base-v2` (or multilingual-e5) | Open weights | 768 / 1024 | Strong asymmetric `query:` / `passage:` style |
| `nomic-embed-text-v1.5` | Open / API | 768 (MRL) | Flexible dim sizing |
| OpenAI `text-embedding-3-small` | Commercial API | 1536 (MRL) | Managed quality; still portable if you own the vectors |
| Cohere `embed-english-v3.0` | Commercial API | 1024 | Explicit document vs query input types |

Chroma’s common local default (`all-MiniLM-L6-v2`, 384-d) is fine for **prototyping**; for sharper finance nuance, compare against BGE/E5 or a small commercial model on a golden set before a full re-index.

#### How do you validate a model choice quickly?

Before indexing millions of rows:

1. Build **10–15 golden queries** (exact category language and indirect symptoms).
2. Index **50–100** representative rows into two temporary collections (two candidate models).
3. Check **top-3 recall** without relying on metadata filters yet.
4. Check **score separation** — relevant hits clearly above unrelated products. If every score sits in a narrow band, the document template may still have too much shared boilerplate or the model may be too generic.

Localhost CCAA today still has an MVP **hash** embedder for CI; professional indexing should swap to a real model under a later story while keeping this document/metadata contract stable.

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

**Localhost Consumer Complaint Datasets (3 months) → search indexes:** [`docs/Runbooks/Localhost/3m-pgvector-chroma.md`](docs/Runbooks/Localhost/3m-pgvector-chroma.md) (#210).

E2E happy path (UI → API → Airflow → callback → UI, SQLite first): see `docs/local-admin-e2e-happy-path.md`. CI smoke: `npm run local:e2e:happy-path:smoke`. Live API probe: `npm run local:e2e:happy-path:probe`. DoD matrix (SQLite / Postgres / MongoDB): `docs/local-admin-e2e-dod-matrix.md` · `npm run local:e2e:dod-matrix:smoke`.

### Local URLs, usernames, and passwords

Defaults from `CICD/Local/*/docker-compose.yaml` and portal/API scripts. **Local-only** — never reuse these in cloud. Copy `Middleware/ConsumerComplaintsHandsOn/.env.example` → `.env` (git-ignored) and fill from this table.

> [!NOTE]
> GitHub’s README sanitizer strips `target="_blank"`, so these links always open in the **same** tab on github.com. Use **Cmd/Ctrl+click** or middle-click for a new tab.

#### Host apps (not Docker)

| Service | URL | Username | Password | Notes |
|---|---|---|---|---|
| Middleware API | http://127.0.0.1:8000 | — | — | `npm run local:handson:middlware:all:start`; OpenAPI at http://127.0.0.1:8000/docs |
| Admin portal | http://127.0.0.1:4200 | — | — | Proxies `/api` → API `:8000` |
| Intellect portal | http://127.0.0.1:4201 | — | — | Proxies `/api` → API `:8000` |
| SQLite operational DB | `Middleware/ConsumerComplaintsHandsOn/.data/operational.sqlite` | — | — | Default when `CCA_OPERATIONAL_STORE` / `CCA_DB_URL` unset |

#### Containers

| Service | URL / connection | Username | Password | `.env` / notes |
|---|---|---|---|---|
| Airflow UI + API | http://127.0.0.1:8080 | `airflow` | `airflow` | `CCA_AIRFLOW_API_BASE_URL`, `CCA_AIRFLOW_API_USERNAME`, `CCA_AIRFLOW_API_PASSWORD` |
| Airflow metadata Postgres | (internal Docker only) | `airflow` | `airflow` | DB `airflow`; not the CCA operational store |
| CCA ops Postgres (+ pgvector) | `postgresql://postgres:postgres@127.0.0.1:5432/cca` | `postgres` | `postgres` | DB `cca`. Set `CCA_OPERATIONAL_STORE=postgres`, `CCA_DB_URL=postgresql+psycopg://postgres:postgres@127.0.0.1:5432/cca`, `CCA_PGVECTOR_URL=postgresql://postgres:postgres@127.0.0.1:5432/cca` |
| MongoDB (complaints) | `mongodb://root:changeme-local@127.0.0.1:27017/?authSource=admin` | `root` | `changeme-local` | **Auth required** or Compass shows an empty Databases list. Paste that URI in Compass (or Username `root` / Password `changeme-local` / Auth DB `admin`). After first boot: `consumer_comp_db.complaints` (empty until DB Ingest). App: `CCA_MONGO_COMPLAINTS_URL=mongodb://root:changeme-local@127.0.0.1:27017/consumer_comp_db?authSource=admin`. Ops-store profile (optional): `CCA_OPERATIONAL_STORE=mongodb`, `CCA_MONGO_OPERATIONAL_URL=…/cca_operational?authSource=admin` |
| Chroma | http://127.0.0.1:8100 (host) | — | — | Host port **8100** → container 8000 (avoids Middleware `:8000`; override with `CCA_CHROMA_PORT`). **Airflow (Docker):** set `CCA_CHROMA_URL=http://host.docker.internal:8100` then Sync secrets — `127.0.0.1` inside the worker is not your Mac |
| Redis Stack | `redis://127.0.0.1:6379/0` | — | — | `CCA_REDIS_URL`. RedisInsight UI: http://127.0.0.1:8001 |

#### Required Middleware `.env` for live Airflow callbacks

| Variable | Example local value | Purpose |
|---|---|---|
| `CCA_CALLBACK_SECRET` | `cca-local-dev-callback-secret` | Shared secret; Airflow callbacks send `X-Callback-Secret` (401 without it). **Localhost fixed value only — never reuse in cloud/M90** (#211) |
| `CCA_API_URL` | `http://host.docker.internal:8000` | Base URL workers use to reach Middleware (Docker Desktop) |
| `CCA_AIRFLOW_API_PASSWORD` | `airflow` | Matches Airflow WWW user (with username `airflow`) |
| `CCA_VECTOR_STORE_PATH` | e.g. absolute path under Airflow data | JSONL vector index (`index_cfpb_all`) |
| `LOCAL_DATA_PATH_CFPB` | `$HOME/runtime_data/apps/datasets/CCA/complains_datasets/imports` | Where CFPB zips land (localhost). Use absolute `$HOME/...` in `.env`; Airflow compose bind-mounts the same path (#212) |
| `CCA_CFPB_SPLIT_SOURCE_PATH_3_MONTHS` | `$HOME/Downloads/temp/complaints_split_3_months_data` | 3-month filter input (M17-0005) |
| `CCA_CFPB_SPLIT_SOURCE_PATH_6_MONTHS` | `$HOME/Downloads/temp/complaints_split_6_months_data` | Reserved for 6-month MIO |
| `CCA_CFPB_SPLIT_SOURCE_PATH_9_MONTHS` | `$HOME/Downloads/temp/complaints_split_9_months_data` | Reserved for 9-month MIO |
| `CCA_CFPB_SPLIT_SOURCE_PATH_12_MONTHS` | `$HOME/Downloads/temp/complaints_split_12_months_data` | Reserved for 12-month MIO |
| `CCA_CFPB_SPLIT_SOURCE_PATH_ALL` | `$HOME/Downloads/temp/complaints_split_all_data` | All MIO download/stage (M17-0005) |
| `CCA_CFPB_SPLIT_SOURCE_PATH` | legacy single-folder alias | Optional fallback if per-MIO var unset |

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
