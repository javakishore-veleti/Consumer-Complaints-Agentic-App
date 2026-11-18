# Localhost runbook: Customer complaints 3 months 2026 → search indexes

**Goal (localhost only):** End-to-end on **Customer complaints 3 months 2026** only — filter → Mongo ingest → pgvector + Chroma indexes. Do **not** use any other MIO for this path.

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

Also ensure local Airflow is up (includes pymongo image):

```bash
cd CICD/Local/airflow && docker compose up -d --build
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
| `CCA_CFPB_SPLIT_SOURCE_PATH_3_MONTHS` | folder (or one file) of CFPB parts for the **3-month** filter |

Sync secrets so Airflow Variables match. Filtered outputs land under `LOCAL_DATA_PATH_CFPB` as a UTC `YYYY-MM-DD-HH-MM-SS` import-run folder.

### 0.3 Open the UIs

1. Admin (**Consumer Complaints Administration**) → http://127.0.0.1:4200  
2. Airflow → http://127.0.0.1:8080 (`airflow` / `airflow`)  
3. API docs → http://127.0.0.1:8000/docs  

### 0.4 Operations → Sync secrets

1. In Admin open **Operations**.
2. Run **Sync secrets**.
3. Confirm success.
4. Confirm Airflow has `CCA_API_URL=http://host.docker.internal:8000` and `CCA_CALLBACK_SECRET`.

![Airflow Variables after Sync secrets](assets/airflow-variables-after-sync.png)

### 0.5 Confirm DAGs are enabled

http://127.0.0.1:8080/dags — these should be on (3-month MIO bindings):

- `filter_cfpb_3_months`
- `ingest_cfpb_imports_wrapper`
- `index_cfpb_pgvector`
- `index_cfpb_chroma`
- `index_cfpb_redis` (optional for this runbook)

---

## 1. Build the 3-month dataset (Imports)

**Objective:** Filter CFPB input by `Date received` (last 3 months) on **Customer complaints 3 months 2026** only. Creates a landed import-run folder with multi-part `*_3_months.csv.zip` files (not a single monolith zip).

**Input:** `CCA_CFPB_SPLIT_SOURCE_PATH_3_MONTHS` after Sync — folder of parts **or** one `.csv`/`.zip`.

**Where:** **DataSets → Imports**. Expand **Customer complaints 3 months 2026**.

![Customer complaints 3 months 2026 — filter_cfpb_3_months](assets/imports-3-months-filter-cfpb.png)

1. Choose workflow **`filter_cfpb_3_months`**
2. Click **Start workflow**
3. **Refresh status** until **`completed`**
4. Airflow: DAG `filter_cfpb_3_months` = success
5. Under `LOCAL_DATA_PATH_CFPB`, confirm a new `YYYY-MM-DD-HH-MM-SS` folder with `dataset/complaints_part_*_3_months.csv.zip` (many parts is normal)

---

## 2. Publish to MongoDB (DB Ingest)

**Objective:** Load that landed import run into Mongo for the **3-month** MIO.

**Where:** **DataSets → DB Ingest**

1. In **Import runs**, check the **landed** run for this filter (or **Select latest landed**). Already-ingested rows stay disabled.
2. Keep ingest mode **Sequential** unless you intend parallel.
3. Expand **Customer complaints 3 months 2026**.
4. Keep workflow **`ingest_cfpb_imports_wrapper`**.
5. Click **Start ingest** (enabled only when ≥1 landed/failed run is checked).
6. Wait until status shows **`completed`** (not stuck on `requested`/`failed` with a stale message — **Refresh status**).
7. Airflow: `ingest_cfpb_imports_wrapper` → child `ingest_cfpb_all` = success.

Compass (auth required): `mongodb://root:changeme-local@localhost:27017/?authSource=admin` → `consumer_comp_db.complaints`.

---

## 3. Index in Postgres (pgvector)

**Objective:** Index the 3-month Mongo corpus into `complaint_vectors`.

**Where:** **DataSets → Index** (or Imports if Index is reached from there). Expand **Customer complaints 3 months 2026**.

1. Start **`index_cfpb_pgvector`**
2. Wait until **`completed`**
3. Airflow: DAG `index_cfpb_pgvector` = success

```bash
docker exec -it cca-operational-postgres \
  psql -U postgres -d cca -c "SELECT count(*) FROM complaint_vectors;"
```

---

## 4. Index in Chroma

**Objective:** Same corpus into local Chroma (`:8100`) from the **3-month** MIO.

1. Start **`index_cfpb_chroma`**
2. Wait until **`completed`**
3. Airflow: DAG `index_cfpb_chroma` = success

Chroma HTTP: http://127.0.0.1:8100

---

## 5. Definition of Done

| # | Outcome | How you know |
|---|---|---|
| 1 | 3-month parts landed | `filter_cfpb_3_months` **`completed`**; `dataset/complaints_part_*_3_months.csv.zip` under a UTC import-run folder |
| 2 | Documents in Mongo | DB Ingest **`completed`** on 3-month MIO; import run **ingested** |
| 3 | Searchable in Postgres | `index_cfpb_pgvector` **`completed`**; `complaint_vectors` count &gt; 0 |
| 4 | Searchable in Chroma | `index_cfpb_chroma` **`completed`**; Chroma on `:8100` |

**Workflow reference (3-month MIO only)**

| Step | Workflow / DAG |
|---|---|
| Build 3-month dataset | `filter_cfpb_3_months` |
| Publish to Mongo | `ingest_cfpb_imports_wrapper` |
| Postgres vector store | `index_cfpb_pgvector` |
| Chroma vector store | `index_cfpb_chroma` |

---

## If something fails

| Symptom | Fix |
|---|---|
| Admin `:4200` refused | `npm run local:portals:all:start` |
| Callbacks 401 | Sync secrets; matching `CCA_CALLBACK_SECRET` |
| Filter finds no inputs | Point `CCA_CFPB_SPLIT_SOURCE_PATH_3_MONTHS` at a folder with `.csv`/`.zip` (or one file); Sync; retry §1 |
| Start ingest disabled / “select landed runs” | Check a **landed** (or **failed**) import run above, then Start |
| Ingest: `ModuleNotFoundError: pymongo` | `cd CICD/Local/airflow && docker compose up -d --build` |
| Admin shows failed after Airflow success | Refresh status; ensure latest DAGs mounted (finalize ORM fix). Re-run Start ingest if needed |
| Compass shows no databases | Auth URL: `mongodb://root:changeme-local@localhost:27017/?authSource=admin` |
| Index empty | Ingest incomplete; or Mongo / pgvector / Chroma URLs not synced |

Related: root README local credentials · path `docs/Runbooks/Localhost/3m-pgvector-chroma.md`
