# Localhost runbook: Consumer Complaint Datasets (split parts) → search indexes

**Goal (localhost only):** On your **local developer workstation**, stage **pre-split** CFPB part files from a folder you provide, load them into the complaint store (MongoDB), then build **Postgres (pgvector)** and **Chroma** search indexes — each Admin step finishes in Airflow as **`completed`**.

**Why not one huge zip?** Downloading or uploading the full CFPB monolith is slow. You already split it into `complaints_part_*.csv.zip`. This runbook **points Airflow at that folder**; the download workflow **copies every matching part** into the landing directory, then ingest/index use those parts. No monolith download and no date-filter step.

Do these steps **in order**. Wait until each run shows **`completed`** before starting the next.

---

## 0. One-time setup

### 0.1 Stop then start containers, API, and Admin

**Objective:** Bring up a clean localhost stack so Admin, API, and Airflow can talk to each other. Stop first (safe if nothing is running), then start.

From the repo root (Node 22+). Paste **only** these lines into the terminal (explanations are above each group — do not paste trailing comments on the same line as `npm run`, or zsh may pass them as arguments).

Stop first (safe if nothing is running):

```bash
npm run local:portals:all:stop
npm run local:handson:middlware:all:stop
npm run local:containers:chroma:stop
npm run local:containers:mongodb:stop
npm run local:containers:postgres:stop
```

Then start (postgres profile = Airflow + ops Postgres/pgvector; chroma host port 8100; API 8000; Admin 4200):

```bash
npm run local:containers:postgres:start
npm run local:containers:mongodb:start
npm run local:containers:chroma:start
npm run local:api:migrate
npm run local:handson:middlware:all:start
npm run local:portals:all:start
```

### 0.2 Confirm `.env` and your split folder

**Objective:** Middleware and (after Sync secrets) Airflow share the same localhost config, including the **folder of part zips**.

1. Keep your part files in the default source folder (or another folder you choose):

```text
$HOME/Downloads/temp/complaints_split/complaints_part_001.csv.zip
$HOME/Downloads/temp/complaints_split/complaints_part_002.csv.zip
…
```

Stage copies those files into the **landing** dir `LOCAL_DATA_PATH_CFPB` (`…/complains_datasets/imports/`). Airflow bind-mounts both the landing tree and the default Downloads split folder.

2. Confirm `.env` under `Middleware/ConsumerComplaintsHandsOn/` includes:

| Key | Value |
|---|---|
| `CCA_CALLBACK_SECRET` | `cca-local-dev-callback-secret` (**localhost only** — never cloud) |
| `CCA_API_URL` | `http://host.docker.internal:8000` |
| `CCA_AIRFLOW_API_PASSWORD` | `airflow` |
| `CCA_MONGO_COMPLAINTS_URL` | `mongodb://root:changeme-local@host.docker.internal:27017/consumer_comp_db?authSource=admin` |
| `LOCAL_DATA_PATH_CFPB` | absolute path to `…/complains_datasets/imports` |
| `CCA_CFPB_SPLIT_SOURCE_PATH` | default: absolute `$HOME/Downloads/temp/complaints_split` (override in `.env` if your parts live elsewhere) |
| `CCA_PGVECTOR_URL` | `postgresql://postgres:postgres@host.docker.internal:5432/cca` |
| `CCA_CHROMA_URL` | `http://host.docker.internal:8100` *(Airflow workers)* |

3. To **change** the split folder (or any other upserted value): edit Middleware `.env`, restart Middleware, then run **Operations → Sync secrets** again so Airflow Variables match. Admin Sync does not edit the path itself — it copies whatever Middleware currently has in the environment.

### 0.3 Open the UIs

**Objective:** Have Admin, Airflow, and API docs ready in the browser.

1. Admin → http://127.0.0.1:4200  
2. Airflow → http://127.0.0.1:8080 (`airflow` / `airflow`)  
3. API docs → http://127.0.0.1:8000/docs  

### 0.4 In Admin: Operations → Sync secrets

**Objective:** Copy Middleware `.env` values (including `CCA_CFPB_SPLIT_SOURCE_PATH` and landing/index URLs) into **Airflow Variables** so DAGs can stage parts and reach stores. Without this step, stage/ingest/index fail or callbacks return **401**. Re-run Sync whenever you change those `.env` values.

1. In Admin open **Operations**.
2. Run **Sync secrets**.
3. Confirm success in the UI.
4. Confirm in Airflow **Variables**: open http://127.0.0.1:8080/variables — you should see synced names (callback secret masked). Example after a successful Sync:

![Airflow Variables after Sync secrets](assets/airflow-variables-after-sync.png)

Expect at least: `CCA_CALLBACK_SECRET`, `CCA_API_URL`, `LOCAL_DATA_PATH_CFPB`, `CCA_CFPB_SPLIT_SOURCE_PATH`, `CCA_PGVECTOR_URL`, `CCA_CHROMA_URL`. For **Airflow workers**, Chroma/Redis URLs must use `host.docker.internal` (not `127.0.0.1`).

**If Sync fails with HTTP 422:** `missing` = a required `.env` value is empty. `skipped` = optional name unset (OK for `CCA_DB_URL` on SQLite). For **this** runbook, `CCA_CFPB_SPLIT_SOURCE_PATH` must be set (not skipped). Fix `.env`, restart Middleware, Sync again.

Re-run Sync whenever you change `.env` or stop/start containers with `npm run local:containers:*`.

### 0.5 Confirm DAGs are enabled

**Objective:** Admin can start workflows. On a **new** local Airflow install, DAGs are created **enabled**.

Check http://127.0.0.1:8080/dags — these should already be on:

- `download_cfpb_all` (split stage)
- `ingest_cfpb_all`
- `index_cfpb_pgvector`
- `index_cfpb_chroma`

If a toggle is still **paused**, either turn it on once in the UI, or wipe and restart with npm:

```bash
npm run local:containers:postgres:stop
npm run local:containers:postgres:start
npm run local:containers:mongodb:start
npm run local:containers:chroma:start
```

Then Sync secrets again (§0.4).

---

## 1. Stage every part from your folder into the landing directory

**Objective:** Copy all `complaints_part_*.csv.zip` from `CCA_CFPB_SPLIT_SOURCE_PATH` into `LOCAL_DATA_PATH_CFPB`. You are **not** downloading the CFPB monolith from the internet in this runbook.

**Where in Admin:** **DataSets → Imports** (no separate “MIO” left-nav). Expand the accordion row **Customer complaints all 2026** (that is where the stage/download workflow is attached today).

1. Choose workflow **`download_cfpb_all`** and start it  
   (seeded as `source_mode=split` → AppEndpoint `cfpb_stage_split_to_local`)
2. Click **Refresh status** until the row shows **`completed`**
3. Airflow: DAG `download_cfpb_all` last run = success
4. Confirm parts landed under `LOCAL_DATA_PATH_CFPB` (for example `complaints_part_001.csv.zip`, …)

---

## 2. Publish parts to the complaint store (MongoDB)

**Objective:** Read the landed part zips and write complaint documents into Mongo so index workflows have something to search.

**Why MongoDB**

- After step 1 you only have **files on disk**. Intellect / index DAGs do not read those zips directly.
- **Ingest** loads each part into the **complaint MongoDB** (`CCA_MONGO_COMPLAINTS_URL` / `consumer_comp_db`).
- Steps 3–4 (**pgvector** / **Chroma**) **read from Mongo**.

Seeded `ingest_cfpb_all` already loops `complaints_part_*.csv.zip` under the landing path.

**DataSets → Imports** → expand **Customer complaints all 2026** → start **`ingest_cfpb_all`**  
(or use **DB Ingest** if that page is where you prefer to start ingest workflows).

1. Start **`ingest_cfpb_all`**
2. Wait until **`completed`**
3. Airflow: DAG `ingest_cfpb_all` = success

---

## 3. Make complaints searchable in Postgres (vector store)

**Objective:** Copy complaint text from Mongo into the **ops Postgres** vector table (`complaint_vectors`).

**Embeddings (localhost MVP):** no neural model — `hash_embedding` in `Middleware/Airflow-dags/ccaa/vector_index.py` (dim 32).

**DataSets → Imports** → expand **Customer complaints all 2026**:

1. Start **`index_cfpb_pgvector`**
2. Wait until **`completed`**
3. Airflow: DAG `index_cfpb_pgvector` = success

Quick check:

```bash
docker exec -it cca-operational-postgres \
  psql -U postgres -d cca -c "SELECT count(*) FROM complaint_vectors;"
```

---

## 4. Make complaints searchable in Chroma (vector store)

**Objective:** Copy the same Mongo corpus into **local Chroma** (`:8100`). Same `hash_embedding` as step 3.

**DataSets → Imports** → expand **Customer complaints all 2026**:

1. Start **`index_cfpb_chroma`**
2. Wait until **`completed`**
3. Airflow: DAG `index_cfpb_chroma` = success

Chroma HTTP: http://127.0.0.1:8100  

---

## 5. Definition of Done (functional)

| # | Functional outcome | How you know |
|---|---|---|
| 1 | Your split folder was staged into landing | `download_cfpb_all` **`completed`**; `complaints_part_*.csv.zip` under `LOCAL_DATA_PATH_CFPB` |
| 2 | Complaints are documents in Mongo | `ingest_cfpb_all` **`completed`** |
| 3 | Searchable in Postgres vector store | `index_cfpb_pgvector` **`completed`**; `complaint_vectors` count &gt; 0 |
| 4 | Searchable in Chroma | `index_cfpb_chroma` **`completed`**; Chroma on `:8100` |
| 5 | Admin shows real pipeline status | Status strings are API **`completed`** |

**Workflow / DAG reference**

| Functional outcome | Workflow / DAG |
|---|---|
| Stage all parts from folder | `download_cfpb_all` (`source_mode=split`) |
| Publish to Mongo | `ingest_cfpb_all` (part glob) |
| Postgres vector store | `index_cfpb_pgvector` |
| Chroma vector store | `index_cfpb_chroma` |

---

## If something fails

| Symptom | Fix |
|---|---|
| Admin `:4200` refused | `npm run local:portals:all:start` |
| API `:8000` in use | Chroma on **8100** (`npm run local:containers:chroma:start`) |
| Callbacks 401 | Sync secrets; matching `CCA_CALLBACK_SECRET` |
| Stage finds no directory | Set absolute `CCA_CFPB_SPLIT_SOURCE_PATH`; folder must sit under the mounted `complains_datasets` tree; Sync again; restart Airflow via npm if you changed mounts |
| Stage finds no parts | Folder must contain `complaints_part_*.csv.zip` |
| Ingest finds no files | Stage did not land parts under `LOCAL_DATA_PATH_CFPB` |
| Index empty | Ingest incomplete; or Mongo / pgvector / Chroma URLs not synced |

Related: root README local credentials · `docs/PRODUCT_FEATURES.md` (D91 split path) · path `docs/Runbooks/Localhost/3m-pgvector-chroma.md`
