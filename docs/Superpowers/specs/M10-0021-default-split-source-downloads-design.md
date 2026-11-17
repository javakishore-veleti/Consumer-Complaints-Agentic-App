# M10-0021 (#228) Default split source Downloads path

## Decision
1. Default `CCA_CFPB_SPLIT_SOURCE_PATH=$HOME/Downloads/temp/complaints_split`.
2. Local Airflow compose bind-mounts that path.
3. Override in Middleware `.env` → restart API → Admin **Operations → Sync secrets** to refresh Airflow Variables.
