# Localhost runbook: Consumer Complaint Datasets (3 months) → search indexes

**Goal (localhost only):** On your **local developer workstation** (not GitHub, not cloud), land **Consumer Complaint Datasets** for a **3-month** window, load them into the complaint store, then build **Postgres (pgvector)** and **Chroma** search indexes — each Admin step finishes in Airflow as **`completed`**.

Do these steps **in order**. Wait until each run shows **`completed`** before starting the next.

---

## 0. One-time setup

### 0.1 Start containers, API, and Admin

**Objective:** Bring up the localhost stack so Admin, API, and Airflow can talk to each other.

```bash
# From repo root (Node 22+)
npm run local:containers:postgres:start   # Airflow + ops Postgres/pgvector
npm run local:containers:mongodb:start    # complaint Mongo (if not already up)
npm run local:containers:chroma:start     # Chroma on :8100
npm run local:api:migrate
npm run local:handson:middlware:all:start # API :8000
npm run local:portals:all:start           # Admin :4200 (your terminal)
```

### 0.2 Confirm `.env`

**Objective:** Middleware and (after Sync secrets) Airflow share the same localhost config.

Confirm `.env` exists under `Middleware/ConsumerComplaintsHandsOn/` with at least:

| Key | Value |
|---|---|
| `CCA_CALLBACK_SECRET` | `cca-local-dev-callback-secret` (**localhost only** — never cloud) |
| `CCA_API_URL` | `http://host.docker.internal:8000` |
| `CCA_AIRFLOW_API_PASSWORD` | `airflow` |
| `CCA_MONGO_COMPLAINTS_URL` | `mongodb://root:changeme-local@host.docker.internal:27017/consumer_comp_db?authSource=admin` |
| `LOCAL_DATA_PATH_CFPB` | `$HOME/runtime_data/apps/datasets/CCA/complains_datasets/imports` (absolute path in `.env`) |
| `CCA_PGVECTOR_URL` | `postgresql://postgres:postgres@host.docker.internal:5432/cca` |
| `CCA_CHROMA_URL` | `http://host.docker.internal:8100` *(Airflow workers)* |

### 0.3 Open the UIs

**Objective:** Have Admin, Airflow, and API docs ready in the browser.

1. Admin → http://127.0.0.1:4200  
2. Airflow → http://127.0.0.1:8080 (`airflow` / `airflow`)  
3. API docs → http://127.0.0.1:8000/docs  

### 0.4 In Admin: Operations → Sync secrets

**Objective:** Copy Middleware `.env` values (callback secret, `LOCAL_DATA_PATH_CFPB`, Mongo/pgvector/Chroma URLs, etc.) into **Airflow Variables** so DAGs can reach the API and data stores. Without this step, downloads/ingest/index fail or callbacks return **401**.

1. In Admin open **Operations**.
2. Run **Sync secrets** (upsert listed names into Airflow).
3. Confirm success in the UI (no error toast / success message).
4. Confirm in Airflow **Variables**: open http://127.0.0.1:8080/variables — you should see the synced names (callback secret masked; values never shown in Admin Sync). Example after a successful Sync:

![Airflow Variables after Sync secrets](assets/airflow-variables-after-sync.png)

Expect at least: `CCA_CALLBACK_SECRET`, `CCA_API_URL`, `LOCAL_DATA_PATH_CFPB`, `CCA_PGVECTOR_URL`, `CCA_CHROMA_URL`. For **Airflow workers**, `CCA_CHROMA_URL` / `CCA_REDIS_URL` must use `host.docker.internal` (not `127.0.0.1`) — match §0.2, then Sync again if needed.

**If Sync fails with HTTP 422:** the JSON `results` list shows each name’s `outcome`. `missing` = a **required** `.env` value is empty (fix and restart Middleware). `skipped` = optional name unset (OK on localhost SQLite when you are not using a split staging path). Fix `.env`, restart Middleware, then Sync again.

Re-run this step whenever you change `.env` or stop/start the local containers with the `npm run local:containers:*` scripts.

### 0.5 Confirm DAGs are enabled

**Objective:** Admin “Start workflow” can trigger each DAG. On a **new** local Airflow install, DAGs are created **enabled** (not paused).

Check http://127.0.0.1:8080/dags — these should already be on:

- `download_cfpb_all`
- `filter_cfpb_3_months`
- `ingest_cfpb_all`
- `index_cfpb_pgvector`
- `index_cfpb_chroma`

If a toggle is still **paused**, Airflow is remembering an older local database. Either turn the toggle on once in the UI, or wipe and restart the local containers with npm (from the repo root):

```bash
npm run local:containers:postgres:stop    # stops Airflow + ops Postgres (removes volumes by default)
npm run local:containers:postgres:start
# if you also use Mongo / Chroma for this smoke path, start them again:
npm run local:containers:mongodb:start
npm run local:containers:chroma:start
```

Then re-run **Sync secrets** (§0.4) before starting workflows.

---

## 1. Consumer Complaint Datasets — land the full export

**Objective:** Download the full Consumer Complaint Datasets package locally (required before preparing **Customer complaints 3 months 2026**).

Admin → **DataSets → Imports** → MIO **Customer complaints all 2026**

1. Start workflow **`download_cfpb_all`**
2. Click **Refresh** until status is **`completed`**
3. Airflow: DAG `download_cfpb_all` last run = success

---

## 2. Consumer Complaint Datasets — Customer complaints 3 months 2026

**Objective:** Prepare the Managed Information Object **Customer complaints 3 months 2026** from the full export (same name you see in Admin).

Admin → **DataSets → Imports** → MIO **Customer complaints 3 months 2026**

1. Start workflow **`filter_cfpb_3_months`**
2. Wait until **`completed`**
3. Landing file (under `LOCAL_DATA_PATH_CFPB`): `complaints_3_months.csv.zip`

---

## 3. Consumer Complaint Datasets — publish Customer complaints 3 months 2026 to the complaint store (MongoDB)

**Objective:** Turn the on-disk **Customer complaints 3 months 2026** file into **complaint documents** the product can search and index.

**Why MongoDB / what ingest does**

- After steps 1–2 you only have **zip files on disk** under `LOCAL_DATA_PATH_CFPB`. Those files are not queryable by Intellect or the index workflows.
- **Ingest** reads that zip, writes each complaint as a document into the **complaint MongoDB** (`CCA_MONGO_COMPLAINTS_URL` / `consumer_comp_db`). That database is the **source of truth for complaint text** (separate from the Admin/operational store).
- Steps 4–5 (**pgvector** / **Chroma**) **read from Mongo**, not from the zip. Skip or fail ingest → empty indexes.

Seeded `ingest_cfpb_all` looks for `complaints_part_*.csv.zip`. For **Customer complaints 3 months 2026**, point ingest at the filter output once:

Admin → MIO **Customer complaints all 2026** → workflow **`ingest_cfpb_all`**  
(or via API: set that workflow’s config to)

```json
{
  "dataset_code": "CFPB",
  "source_filename": "complaints_3_months.csv.zip",
  "batch_size": 500,
  "app_endpoint_name": "cfpb_ingest_local_to_mongo"
}
```

(Do **not** set `source_filename_glob` for this run.)

1. Start **`ingest_cfpb_all`**
2. Wait until **`completed`**
3. Airflow: DAG `ingest_cfpb_all` = success

---

## 4. Consumer Complaint Datasets — make complaints searchable in Postgres (vector store)

**Objective:** Copy complaint text from Mongo into the **ops Postgres vector store** so you can run local similarity search against **Customer complaints 3 months 2026** (and whatever else was ingested).

**What this is (not “Index → pgvector” as a product name)**  
Postgres here is the **operational DB** with the **pgvector** extension. The workflow stores each complaint id + text + embedding in a vector table (`complaint_vectors` by default).

**Embeddings — what / where / how (localhost MVP)**

| Question | Answer |
|---|---|
| What model? | **No neural / paid embedding model.** Localhost uses deterministic **`hash_embedding`** (SHA-256–based pseudo-vectors), dimension **32**. |
| Where is the code? | `Middleware/Airflow-dags/ccaa/vector_index.py` — `hash_embedding()`, called from `index_complaint_docs()`. |
| How does the DAG use it? | Reads complaint docs from Mongo → builds text → `hash_embedding(text)` → upserts into Postgres via `open_vector_store(backend="pgvector")`. |
| Why this way? | CI/laptop friendly (D88/D92/D94): no GPU, no API keys. Cloud embedding models stay **M90**. |

Admin → MIO **Customer complaints all 2026**

1. Start workflow **`index_cfpb_pgvector`**
2. Wait until **`completed`**
3. Airflow: DAG `index_cfpb_pgvector` = success

Quick check (host):

```bash
docker exec -it cca-operational-postgres \
  psql -U postgres -d cca -c "SELECT count(*) FROM complaint_vectors;"
```

(If empty, check Airflow task logs / Sync secrets for `CCA_PGVECTOR_URL` + Mongo URL.)

---

## 5. Consumer Complaint Datasets — make complaints searchable in Chroma (vector store)

**Objective:** Copy the **same** Mongo complaint corpus into **local Chroma** so you have a second localhost vector store (separate container on `:8100`).

**What this is (not “Index → Chroma” as a product name)**  
Chroma is an opt-in **document + embedding** store. Same complaint texts as step 4; different backend.

**Embeddings — what / where / how**  
**Same as step 4:** `hash_embedding` in `Middleware/Airflow-dags/ccaa/vector_index.py` (dim 32). The Chroma DAG calls `open_vector_store(backend="chroma")` and upserts those vectors — it does **not** call OpenAI/HuggingFace/etc.

Admin → MIO **Customer complaints all 2026**

1. Start workflow **`index_cfpb_chroma`**
2. Wait until **`completed`**
3. Airflow: DAG `index_cfpb_chroma` = success

Chroma HTTP: http://127.0.0.1:8100  

---

## 6. Definition of Done (functional)

**You are done when all of the following are true** (operator view — not “DAGs ran” alone):

| # | Functional outcome | How you know |
|---|---|---|
| 1 | Full Consumer Complaint Datasets export is on **localhost** (your workstation disk) | Admin MIO **Customer complaints all 2026** last run for land/download is **`completed`** |
| 2 | **Customer complaints 3 months 2026** dataset exists as a derived file | Admin MIO **Customer complaints 3 months 2026** prepare step is **`completed`**; `complaints_3_months.csv.zip` under `LOCAL_DATA_PATH_CFPB` |
| 3 | Those complaints are **published as documents** in the complaint store | Ingest step **`completed`**; Mongo has complaint docs (index steps have something to read) |
| 4 | Complaints are **searchable in Postgres vector store** | `index_cfpb_pgvector` **`completed`**; `complaint_vectors` row count &gt; 0 |
| 5 | Complaints are **searchable in Chroma** | `index_cfpb_chroma` **`completed`**; Chroma reachable on `:8100` |
| 6 | Admin shows real pipeline status | Every status string is API **`completed`** (never invented in the UI) |

**Workflow / DAG reference** (technical ids behind the functional steps above):

| Functional outcome | Workflow / DAG |
|---|---|
| Land full export | `download_cfpb_all` |
| Customer complaints 3 months 2026 | `filter_cfpb_3_months` |
| Publish to complaint store (Mongo) | `ingest_cfpb_all` (3m filename) |
| Postgres vector store | `index_cfpb_pgvector` |
| Chroma vector store | `index_cfpb_chroma` |

---

## If something fails

| Symptom | Fix |
|---|---|
| Admin `:4200` refused | You must start portals: `npm run local:portals:all:start` |
| API `:8000` in use | Chroma must be on **8100** (`npm run local:containers:chroma:start`) |
| Callbacks 401 | Sync secrets; `CCA_CALLBACK_SECRET` must match |
| Engine start 502 | Airflow down or wrong `CCA_AIRFLOW_API_*` |
| Ingest finds no files | Wrong landing path / still using part glob instead of `complaints_3_months.csv.zip` |
| Index empty | Ingest did not complete; or `CCA_MONGO_COMPLAINTS_URL` / `CCA_PGVECTOR_URL` / `CCA_CHROMA_URL` not synced into Airflow |

Related: root README local credentials tables · `docs/local-admin-e2e-happy-path.md` · issue #210 · path `docs/Runbooks/Localhost/3m-pgvector-chroma.md`
