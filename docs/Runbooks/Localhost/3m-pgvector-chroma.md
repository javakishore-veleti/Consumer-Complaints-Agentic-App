# Localhost runbook: 3-month CFPB → pgvector + Chroma

Goal: on **this machine only**, get a **3-month** CFPB zip, load it into Mongo, then index into **ops Postgres (pgvector)** and **Chroma**, with each step finishing in Airflow.

Do these steps **in order**. Wait until each run shows **completed** before starting the next.

---

## 0. One-time setup

```bash
# From repo root (Node 22+)
npm run local:containers:postgres:start   # Airflow + ops Postgres/pgvector
npm run local:containers:mongodb:start    # complaint Mongo (if not already up)
npm run local:containers:chroma:start     # Chroma on :8100
npm run local:api:migrate
npm run local:handson:middlware:all:start # API :8000
npm run local:portals:all:start           # Admin :4200 (your terminal)
```

Confirm `.env` exists under `Middleware/ConsumerComplaintsHandsOn/` with at least:

| Key | Value |
|---|---|
| `CCA_CALLBACK_SECRET` | your secret |
| `CCA_API_URL` | `http://host.docker.internal:8000` |
| `CCA_AIRFLOW_API_PASSWORD` | `airflow` |
| `CCA_MONGO_COMPLAINTS_URL` | `mongodb://root:changeme-local@host.docker.internal:27017/consumer_comp_db?authSource=admin` |
| `LOCAL_DATA_PATH_CFPB` | e.g. `/opt/airflow/logs/cfpb` |
| `CCA_PGVECTOR_URL` | `postgresql://postgres:postgres@host.docker.internal:5432/cca` |
| `CCA_CHROMA_URL` | `http://host.docker.internal:8100` *(Airflow workers)* |

Open:

1. Admin → http://127.0.0.1:4200  
2. Airflow → http://127.0.0.1:8080 (`airflow` / `airflow`)  
3. API docs → http://127.0.0.1:8000/docs  

In Admin: **Operations → Sync secrets**.

In Airflow: unpause these DAGs if paused:

- `download_cfpb_all`
- `filter_cfpb_3_months`
- `ingest_cfpb_all`
- `index_cfpb_pgvector`
- `index_cfpb_chroma`

---

## 1. Download All (needed before 3-month filter)

Admin → **DataSets → Imports** → MIO **Customer complaints all 2026**

1. Start workflow **`download_cfpb_all`**
2. Click **Refresh** until status is **`completed`**
3. Airflow: DAG `download_cfpb_all` last run = success

---

## 2. Build the 3-month zip

Admin → same page → MIO **Customer complaints 3 months 2026**

1. Start workflow **`filter_cfpb_3_months`**
2. Wait until **`completed`**
3. Result file (inside Airflow data path): `complaints_3_months.csv.zip`

---

## 3. Ingest the 3-month zip into Mongo

Seeded `ingest_cfpb_all` looks for `complaints_part_*.csv.zip`. For **3 months**, point it at the filter output once:

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

## 4. Index → pgvector

Admin → MIO **Customer complaints all 2026**

1. Start **`index_cfpb_pgvector`**
2. Wait until **`completed`**
3. Airflow: DAG `index_cfpb_pgvector` = success

Quick check (host):

```bash
docker exec -it cca-operational-postgres \
  psql -U postgres -d cca -c "SELECT count(*) FROM complaint_vectors;"
```

(Table name may match your store default; if empty, check Airflow task logs.)

---

## 5. Index → Chroma

Admin → MIO **Customer complaints all 2026**

1. Start **`index_cfpb_chroma`**
2. Wait until **`completed`**
3. Airflow: DAG `index_cfpb_chroma` = success

Chroma UI/API: http://127.0.0.1:8100  

---

## 6. Done checklist

| Step | Workflow / DAG | Where to confirm |
|---|---|---|
| Download All | `download_cfpb_all` | Admin All MIO + Airflow |
| 3-month zip | `filter_cfpb_3_months` | Admin 3 months MIO + Airflow |
| Mongo load | `ingest_cfpb_all` (3m filename) | Admin All MIO + Airflow |
| pgvector | `index_cfpb_pgvector` | Admin All MIO + Airflow + Postgres |
| Chroma | `index_cfpb_chroma` | Admin All MIO + Airflow + `:8100` |

Every Admin status must be the API string **`completed`** (not invented in the UI).

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
