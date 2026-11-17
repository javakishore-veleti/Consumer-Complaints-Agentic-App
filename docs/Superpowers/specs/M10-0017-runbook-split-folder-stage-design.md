# M10-0017 (#224) Runbook 3m via split folder stage

## Decision
1. Primary localhost smoke path: set `CCA_CFPB_SPLIT_SOURCE_PATH` to a folder of `complaints_part_*.csv.zip` → `download_cfpb_all` (`source_mode=split`) stages all matching parts into `LOCAL_DATA_PATH_CFPB` → ingest → index.
2. Do not use monolith zip download + `filter_cfpb_3_months` as the primary path.
3. Airflow compose mounts `$HOME/runtime_data/apps/datasets/CCA/complains_datasets` so both landing and split folders are visible in workers.
