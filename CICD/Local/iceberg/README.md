# Local Apache Iceberg + Spark (Raw Zone runtime)

**Story:** M40-0002 #311  
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

## Start / stop

```bash
cd CICD/Local/iceberg
docker compose up -d
docker compose ps
docker compose down
```

Optional named start via the local orchestrator:

```bash
CICD/Local/docker-all-up.sh iceberg
```

## Verify catalog / quickstart-style read

```bash
docker exec -it cca-spark-iceberg spark-sql
```

Example (demo catalog from the image; adjust once Raw DDL is created in a follow-on ingest story):

```sql
SHOW NAMESPACES IN demo;
-- After Raw tables exist (future ingest DAG story):
-- SELECT COUNT(*) FROM demo.raw.cfpb_complaints_3m;
```

PySpark:

```bash
docker exec -it cca-spark-iceberg pyspark
```

```python
spark.sql("SHOW NAMESPACES IN demo").show()
```

## How Airflow PySpark workers should connect (contract)

**No DAG changes in #311.** Future Raw ingest DAGs should use this contract:

| Concern | Value |
|---|---|
| Spark runtime | `cca-spark-iceberg` container (exec, Spark Connect, or shared Docker network) |
| Lift Zone input | Host: `$HOME/runtime_data/apps/datasets/CCA/complains_datasets` · In Spark: `/lift` |
| Warehouse | Compose volume `./warehouse` → `/home/iceberg/warehouse` |
| Iceberg REST (optional) | `http://cca-iceberg-rest:8181` on `cca-iceberg-net` |
| Object store endpoint | `http://object-store:9000` (credentials `admin` / `password` — local only) |
| Target tables | `raw.cfpb_complaints_{3m,6m,9m,12m,all}` per `docs/DataArchitecture.md` |

Recommended Airflow Variables / secrets (names only; set later when DAGs land):

- `CCA_LIFT_ZONE` — host Lift Zone root  
- `CCA_ICEBERG_WAREHOUSE` — host path to `CICD/Local/iceberg/warehouse`  
- `CCA_ICEBERG_SPARK_MASTER` / connect URL — once Spark Connect is used from Airflow workers  

Airflow already mounts the Lift Zone tree; Raw DAGs should **not** re-download CFPB zip files when the Lift Zone object exists.

## Warehouse & notebooks

- `./warehouse/` — local Iceberg/Parquet data (gitignored except `.gitkeep`)  
- `./notebooks/` — optional notebooks (gitignored except `.gitkeep`)  

## Security note

Default object-store credentials are **local lab only**. Do not reuse in cloud.
