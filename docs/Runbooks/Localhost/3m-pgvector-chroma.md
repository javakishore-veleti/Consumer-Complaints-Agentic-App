# Localhost runbook: Customer complaints 3 months 2026 → search indexes

**Goal (localhost only):** On your workstation, build the **Customer complaints 3 months 2026** dataset, load it into MongoDB, then build **Postgres (pgvector)** and **Chroma** indexes. Each Admin step finishes as **`completed`**.

Do these steps **in order**. Wait until each run shows **`completed`** before starting the next.

---

## 0. One-time setup

### 0.1 Stop then start containers, API, and Admin

From the repo root (Node 22+). Paste **only** these lines (no trailing comments on the same line as `npm run`).

Stop first (safe if nothing is running):

```bash
npm run local:portals:all:stop
npm run local:handson:middlware:all:stop
npm run local:containers:chroma:stop
npm run local:containers:mongodb:stop
npm run local:containers:postgres:stop
```

Then start:

```bash
npm run local:containers:postgres:start
npm run local:containers:mongodb:start
npm run local:containers:chroma:start
npm run local:api:migrate
npm run local:handson:middlware:all:start
npm run local:portals:all:start
```

### 0.2 Confirm `.env`

Under `Middleware/ConsumerComplaintsHandsOn/`, confirm at least:

| Key | Value |
|---|---|
| `CCA_CALLBACK_SECRET` | `cca-local-dev-callback-secret` (**localhost only**) |
| `CCA_API_URL` | `http://host.docker.internal:8000` |
| `CCA_AIRFLOW_API_PASSWORD` | `airflow` |
| `CCA_MONGO_COMPLAINTS_URL` | `mongodb://root:changeme-local@host.docker.internal:27017/consumer_comp_db?authSource=admin` |
| `LOCAL_DATA_PATH_CFPB` | absolute path to `…/complains_datasets/imports` |
| `CCA_PGVECTOR_URL` | `postgresql://postgres:postgres@host.docker.internal:5432/cca` |
| `CCA_CHROMA_URL` | `http://host.docker.internal:8100` |

Filter reads `complaints.csv.zip` from `LOCAL_DATA_PATH_CFPB` and writes `complaints_3_months.csv.zip` there. That All zip must already be on disk before step 1 (from a prior download/stage).

### 0.3 Open the UIs

1. Admin → http://127.0.0.1:4200  
2. Airflow → http://127.0.0.1:8080 (`airflow` / `airflow`)  
3. API docs → http://127.0.0.1:8000/docs  

### 0.4 Operations → Sync secrets

1. In Admin open **Operations**.
2. Run **Sync secrets**.
3. Confirm success.

![Airflow Variables after Sync secrets](assets/airflow-variables-after-sync.png)

### 0.5 Confirm DAGs are enabled

http://127.0.0.1:8080/dags — these should be on:

- `filter_cfpb_3_months`
- `ingest_cfpb_all` / `ingest_cfpb_imports_wrapper`
- `index_cfpb_pgvector`
- `index_cfpb_chroma`

---

## 1. Build the 3-month dataset

**Objective:** From the All zip on disk, create `complaints_3_months.csv.zip` (last 3 months by `Date received`).

**Where in Admin:** **DataSets → Imports**. Expand **Customer complaints 3 months 2026**.

![Customer complaints 3 months 2026 — filter_cfpb_3_months](assets/imports-3-months-filter-cfpb.png)

1. Choose workflow **`filter_cfpb_3_months`**
2. Click **Start workflow**
3. Click **Refresh status** until the row shows **`completed`**
4. Airflow: DAG `filter_cfpb_3_months` = success
5. Confirm `complaints_3_months.csv.zip` under `LOCAL_DATA_PATH_CFPB`

---

## 2. Publish to MongoDB (complaint store)

**Objective:** Load the 3-month zip into Mongo so index workflows have documents to search.

**Where in Admin:** **DataSets → DB Ingest**

1. Select the landed import / dataset for this run (if the Import runs list is shown)
2. Prefer workflow **`ingest_cfpb_imports_wrapper`** (or **`ingest_cfpb_all`** if that is what your row offers)
3. Click **Start ingest**
4. Wait until status shows **`completed`**
5. Airflow: matching ingest DAG = success

---

## 3. Index in Postgres (pgvector)

**Objective:** Copy complaint text from Mongo into `complaint_vectors`.

**Where in Admin:** **DataSets → Imports** (or **Index**, if your build shows it there).

1. Start **`index_cfpb_pgvector`**
2. Wait until **`completed`**
3. Airflow: DAG `index_cfpb_pgvector` = success

```bash
docker exec -it cca-operational-postgres \
  psql -U postgres -d cca -c "SELECT count(*) FROM complaint_vectors;"
```

---

## 4. Index in Chroma

**Objective:** Copy the same Mongo corpus into local Chroma (`:8100`).

1. Start **`index_cfpb_chroma`**
2. Wait until **`completed`**
3. Airflow: DAG `index_cfpb_chroma` = success

Chroma HTTP: http://127.0.0.1:8100

---

## 5. Definition of Done

| # | Outcome | How you know |
|---|---|---|
| 1 | 3-month zip exists | `filter_cfpb_3_months` **`completed`**; `complaints_3_months.csv.zip` under landing |
| 2 | Documents in Mongo | ingest **`completed`** |
| 3 | Searchable in Postgres | `index_cfpb_pgvector` **`completed`**; `complaint_vectors` count &gt; 0 |
| 4 | Searchable in Chroma | `index_cfpb_chroma` **`completed`**; Chroma on `:8100` |

**Workflow reference**

| Step | Workflow / DAG |
|---|---|
| Build 3-month dataset | `filter_cfpb_3_months` |
| Publish to Mongo | `ingest_cfpb_imports_wrapper` / `ingest_cfpb_all` |
| Postgres vector store | `index_cfpb_pgvector` |
| Chroma vector store | `index_cfpb_chroma` |

---

## If something fails

| Symptom | Fix |
|---|---|
| Admin `:4200` refused | `npm run local:portals:all:start` |
| Callbacks 401 | Sync secrets; matching `CCA_CALLBACK_SECRET` |
| Filter finds no All zip | Put `complaints.csv.zip` under `LOCAL_DATA_PATH_CFPB`, then retry step 1 |
| Index empty | Ingest incomplete; or Mongo / pgvector / Chroma URLs not synced |

Related: root README local credentials · path `docs/Runbooks/Localhost/3m-pgvector-chroma.md`
