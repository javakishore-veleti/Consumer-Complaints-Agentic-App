# M55-0009 Curated OOM / Docker headroom — design

**Story:** #387 · **Date:** 2026-11-19

## Problem

After M55-0008 (broadcast join, no Python UDFs, `--driver-memory 4g`), curated still exits 137. Evidence:

- MemoryStore capacity rose from ~434 MiB → **2.2 GiB** (4g flag applied).
- `docker inspect cca-spark-iceberg` → **`OOMKilled=true`**.
- Docker Desktop limit ≈ **7.65 GiB** shared across Airflow, Mongo, Kafka, Iceberg, etc. Idle stack already uses most of that; a 4 GiB Spark driver tips the VM OOM killer.

Root cause: **Docker VM memory ceiling**, not missing broadcast.

## Design

1. **Default driver memory `2g`** via `CCA_SPARK_DRIVER_MEMORY` (override still allowed). Shell curated script matches.
2. **Spark confs on every lakehouse `spark-submit`:**  
   `spark.sql.shuffle.partitions=8`, `spark.sql.adaptive.enabled=true`, `spark.driver.maxResultSize=512m`.
3. **Curated script:** set the same confs on the session; keep broadcast join; avoid extra full DF caches.
4. **Docs:** one paragraph in `CICD/Local/iceberg/README.md` — curated hydrate needs ~2 GiB Spark headroom; on ~8 GiB Docker, stop unused stacks or raise Docker memory; override with `CCA_SPARK_DRIVER_MEMORY`.

## Out of scope

- Iceberg UI container (separate story).
- Changing Docker Desktop settings from code.
- Raising container `mem_limit` (limit is the Docker VM, not a compose cap).

## Acceptance

Admin re-run of `hydrate_curated_iceberg_3m` completes with rows > 0; container not OOMKilled.
