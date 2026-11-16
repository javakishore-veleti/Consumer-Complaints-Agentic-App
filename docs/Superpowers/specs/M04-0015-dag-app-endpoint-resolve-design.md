# M04-0015 (#161) DAGs resolve from/to via catalog and AppEndpoints

Decision **D87**. Next free: **D88**.

## Goal

Download/ingest DAGs prefer `config_used.app_endpoint_name` → `app_endpoints` row → resolve from/to via location id or env-var name (local/HTTP only). Fall back to existing `dataset_code` + locations when unset.

## D87

1. `ccaa/db_reader.py`: `load_app_endpoint_by_name`, `load_location_by_id`, `resolve_endpoint_paths` (from URL or env; to landing Path or env name).
2. `download_cfpb_all` / `ingest_cfpb_all` use AppEndpoint when `app_endpoint_name` present.
3. Alembic `0014` + Mongo: set `app_endpoint_name` on download/ingest workflow configs; seed ingest AppEndpoint `cfpb_ingest_local_to_mongo` (local landing → `CCA_MONGO_COMPLAINTS_URL`).
4. Unit tests for helpers; DAG files reference resolver.

## Out of scope

Cloud locations (M06), Admin UX copy (#162).
