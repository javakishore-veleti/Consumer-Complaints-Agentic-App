# Local Apache Iceberg + Spark (Raw Zone runtime)

**Stories:** M40-0002 #311 (Docker stack) · M45-0001 #320 (Raw DDL + npm start/stop)  
**Architecture:** `docs/DataArchitecture.md` (Lift Zone → Iceberg Raw/Bronze)  
**Upstream guide:** [Iceberg Spark quickstart](https://iceberg.apache.org/spark-quickstart/#reading-data-from-a-table)

## What this stack provides

| Service | Container | Host port (default) | Role |
|---|---|---|---|
| Spark + Iceberg | `cca-spark-iceberg` | UI `18080`, notebook `18888`, connect `10000`/`10001` | PySpark / SparkSQL for Raw hydration |
| Iceberg REST | `cca-iceberg-rest` | `8181` | REST catalog fixture (quickstart) |
| Object store | `cca-iceberg-object-store` | S3 `9000`, console `9001` | Warehouse object storage (MinIO-compatible alias) |

Ports are remapped so they do **not** collide with local Airflow (`8080`) or Middleware API (`8000`).

## Lift Zone wiring (no re-download)

Existing Airflow download/filter workflows already land CFPB CSV **zip** files under:

```text
${HOME}/runtime_data/apps/datasets/CCA/complains_datasets/
```

(see Airflow compose `LOCAL_DATA_PATH_CFPB` / imports tree). That tree is the **Lift Zone**.

This compose bind-mounts it **read-only** into the Spark container as:

```text
/lift
```

Override the host path if needed:

```bash
export CCA_LIFT_ZONE="$HOME/runtime_data/apps/datasets/CCA/complains_datasets"
```

Raw ingest jobs should **read zips from `/lift/...`** (or the host Lift Zone path from outside Docker) and write Iceberg tables into the warehouse — never mutate Lift Zone files in place.

## Start / stop / status (npm — preferred)

From the **repo root**:

```bash
npm run local:containers:iceberg:start
npm run local:containers:iceberg:status
npm run local:containers:iceberg:stop
```

`stop` uses `--keep-volumes` so the warehouse is retained. Profile `iceberg` is defined in `CICD/Local/profiles.map` and is **not** part of the default sqlite/postgres profiles.

Equivalent orchestrator form:

```bash
CICD/Local/docker-all-up.sh --profile iceberg
CICD/Local/docker-all-status.sh --profile iceberg
CICD/Local/docker-all-down.sh --keep-volumes --profile iceberg
```

Direct compose (also fine):

```bash
cd CICD/Local/iceberg
docker compose up -d
docker compose ps
docker compose down
```

## Apply Raw DDL (M45-0001 / #320)

Creates namespace `demo.raw` and tables:

- `demo.raw.cfpb_complaints_{3m,6m,9m,12m,all}` — 21 columns, `PARTITIONED BY (months(date_received))`
- `demo.raw.cfpb_complaints_quarantine` — same schema, unpartitioned

```bash
npm run local:containers:iceberg:start
npm run local:iceberg:apply-raw-ddl
```

Static template check (no Docker):

```bash
bash CICD/Local/iceberg/scripts/verify_raw_ddl_templates.sh
```

## Hydrate Raw 3m from Lift Zone (M45-0002 / #321)

Requires iceberg containers up and Raw DDL applied. Reads latest `/lift/imports/*/dataset/*3_months*.csv.zip`, stages CSVs, writes `demo.raw.cfpb_complaints_3m` (+ quarantine).

```bash
npm run local:containers:iceberg:start
npm run local:iceberg:apply-raw-ddl
npm run local:iceberg:hydrate-raw-3m
```

Optional smoke limit:

```bash
CCA_RAW_LIMIT=1000 npm run local:iceberg:hydrate-raw-3m
```

Header-map unit check (no Docker):

```bash
bash CICD/Local/iceberg/scripts/verify_hydrate_raw_headers.sh
```

## Prove 3m count reconcile (M45-0004 / #323)

```bash
npm run local:iceberg:prove-raw-3m
```

Expected PASS line: Lift zip row count equals `SELECT COUNT(*) FROM demo.raw.cfpb_complaints_3m`, mandatory-key bad rows = 0. Evidence file: `runtime_data/tmp/raw-3m-proof-*.txt`.

Verified locally 2026-11-19: **1,970,702** Lift rows → **1,970,702** Iceberg rows; quarantine **0**; bad keys **0**.

```sql
SELECT COUNT(*) FROM demo.raw.cfpb_complaints_3m;
-- 1970702
```

## Refined 3m with signature_id (M46-0001 / #324)

Requires Raw 3m hydrated first (`npm run local:iceberg:prove-raw-3m` or hydrate).

```bash
npm run local:iceberg:apply-refined-ddl
npm run local:iceberg:hydrate-refined-3m
npm run local:iceberg:prove-refined-3m
```

Operator demo:

```sql
SELECT COUNT(*) AS n, COUNT(DISTINCT signature_id) AS u_sig
FROM demo.refined.cfpb_complaints_3m;
```

Verified 2026-11-19: **n=1,970,702**, **u_sig=6,716**, null `signature_id`=0 (matches Raw).

## Taxonomy + Mode 2 (M47-0001 / #325)

Requires refined 3m. Seeds 12 Money Topics, product crosswalk (~55 U_prod), and `semantic_signatures` (~2,924 U_sig).

```bash
npm run local:iceberg:prove-taxonomy-mode2-3m
```

Demo join (Capital One → primary_money_topic) is printed by the prove script.

Verified 2026-11-19: topics=**12**, crosswalk=**55**, semantic_signatures=**2,924**.

## Curated 3m Money Topics (M48-0001 / #326)

Requires refined + taxonomy Mode 2. Joins signatures and assigns `parent_org_id`.

```bash
npm run local:iceberg:prove-curated-3m
```

Demo:

```sql
SELECT primary_money_topic, COUNT(*) AS n
FROM demo.curated.cfpb_complaints_3m
GROUP BY primary_money_topic
ORDER BY n DESC;
```

Verified 2026-11-19: curated=**1,970,702**; null topics/org=0; Capital One Money Topic group-by works.

### Docker memory headroom (M55-0009)

Curated hydrate runs Spark inside `cca-spark-iceberg`. Docker Desktop often caps the VM at ~**8 GiB** shared with Airflow, Mongo, Kafka, etc. A **4g** driver can **OOMKill** the Spark container (`exit 137`, `OOMKilled=true`) even when the join itself is correct.

Defaults: `--driver-memory` **2g**, `spark.sql.shuffle.partitions=8`, AQE on. Override with `CCA_SPARK_DRIVER_MEMORY` (e.g. `4g`) only if Docker memory is raised or unused stacks are stopped.

## Chroma semantic signatures catalog (M49-0001 / #336)

Requires taxonomy Mode 2 (`semantic_signatures` ~2,924). Indexes the **catalog** into Chroma collection `cfpb_semantic_signatures` (not 19M complaint rows). Embeddings: local MVP `hash_embedding`.

```bash
npm run local:containers:chroma:start
npm run local:iceberg:hydrate-chroma-signatures-3m
npm run local:iceberg:prove-chroma-signatures-3m
```

`CCA_CHROMA_URL` defaults to `http://127.0.0.1:8100`.

Verified 2026-11-19: chroma **cfpb_semantic_signatures**=**2,924** (= taxonomy U_sig); sample query returns `signature_id` + Money Topic metadata.


## Query AST Gateway golden (M50-0001 / #338)

Requires curated 3m. Compiles Neutral Query AST → SparkSQL COUNT against curated; k-anonymity n≥10.

```bash
npm run local:iceberg:prove-query-ast-golden-3m
```

Golden case: Capital One `parent_org_id` + Credit Cards → **exact_count=3844** (verified 2026-11-19).

## Airflow DAG (M45-0003 / #322)

DAG id: `hydrate_raw_iceberg_3m` (`Middleware/Airflow-dags/hydrate_raw_iceberg_3m.py`).

Flow: sense Lift 3m zips → pre-ingest gate → docker-exec Spark hydrate → DQ → cleanup staging.

Local Airflow compose mounts `/var/run/docker.sock` so workers can exec into `cca-spark-iceberg`. Spark compose mounts `./scripts` at `/opt/cca/iceberg/scripts`. Rebuild Airflow image after pull (`docker compose up -d --build` under `CICD/Local/airflow`) so the `docker` Python SDK is present.

## Verify catalog / tables

```bash
docker exec -it cca-spark-iceberg spark-sql
```

```sql
SHOW NAMESPACES IN demo;
SHOW TABLES IN demo.raw;
-- After Raw hydrate (M45-0002+):
-- SELECT COUNT(*) FROM demo.raw.cfpb_complaints_3m;
```

PySpark:

```bash
docker exec -it cca-spark-iceberg pyspark
```

```python
spark.sql("SHOW TABLES IN demo.raw").show()
```

## How Airflow PySpark workers should connect (contract)

**No DAG in #320.** Future Raw ingest DAGs (#322) should use this contract:

| Concern | Value |
|---|---|
| Spark runtime | `cca-spark-iceberg` container (exec, Spark Connect, or shared Docker network) |
| Lift Zone input | Host: `$HOME/runtime_data/apps/datasets/CCA/complains_datasets` · In Spark: `/lift` |
| Warehouse | Compose volume `./warehouse` → `/home/iceberg/warehouse` |
| Iceberg REST (optional) | `http://cca-iceberg-rest:8181` on `cca-iceberg-net` |
| Object store endpoint | `http://object-store:9000` (credentials `admin` / `password` — local only) |
| Target tables | `demo.raw.cfpb_complaints_{3m,6m,9m,12m,all}` per `docs/DataArchitecture.md` |

Recommended Airflow Variables / secrets (names only; set when DAGs land):

- `CCA_LIFT_ZONE` — host Lift Zone root  
- `CCA_ICEBERG_WAREHOUSE` — host path to `CICD/Local/iceberg/warehouse`  
- `CCA_ICEBERG_SPARK_MASTER` / connect URL — once Spark Connect is used from Airflow workers  

Airflow already mounts the Lift Zone tree; Raw DAGs should **not** re-download CFPB zip files when the Lift Zone object exists.

## Warehouse & notebooks

- `./warehouse/` — local Iceberg/Parquet data (gitignored except `.gitkeep`)  
- `./notebooks/` — optional notebooks (gitignored except `.gitkeep`)  
- `./sql/create_raw_tables.sql` — Raw DDL templates  
- `./scripts/apply_raw_ddl.sh` — apply DDL inside `cca-spark-iceberg`

## Security note

Default object-store credentials are **local lab only**. Do not reuse in cloud.
