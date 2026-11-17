# M10-0005 (#212) Localhost CFPB imports path + Airflow mount

## Decision

1. **Fixed host landing dir (localhost):**  
   `$HOME/runtime_data/apps/datasets/CCA/complains_datasets/imports`  
   (operator spelling `complains_datasets` kept as given.)

2. **`LOCAL_DATA_PATH_CFPB`** for local Middleware `.env` / Airflow Variables = that path expanded to an absolute `$HOME/...` value.

3. **Airflow compose** bind-mounts the same host path to the **same absolute path** inside workers so DAGs writing `LOCAL_DATA_PATH_CFPB` succeed.

4. **Docs** (README, runbook, `.env.example`) document this path — not `/opt/airflow/logs/cfpb`.

5. **Out of scope:** cloud paths (M90); changing folder spelling.
