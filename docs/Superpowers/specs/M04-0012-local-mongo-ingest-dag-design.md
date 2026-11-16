# M04-0012 (#158) Local Mongo ingest DAG + callbacks

Decisions: D10, D12, D20, D30, D51, D58–D60, D63, D67 and **D86**. Next free decision: **D87**.

## Goal

Airflow DAG reads a landed CFPB zip/CSV and upserts complaint documents into **local Mongo** in batches; reports status (and volume) via existing callback API. API never bulk-writes complaints.

## Approaches

| | Approach | Trade-off |
|---|---|---|
| A | API bulk-write endpoint | Violates F6 / D12 |
| B (chosen) | Airflow DAG + `pymongo` batches + callbacks | Matches D20; same `ccaa/` pattern as download |
| C | Spark | Premature (D20) |

## Decision D86 (summary)

1. **Env / Variable `CCA_MONGO_COMPLAINTS_URL`** — Mongo URI for the **complaint-document** database (not `CCA_MONGO_OPERATIONAL_URL`). Listed in `Airflow_Variables_Upsert.txt` and `.env.example` with `[upsert]`. URI path database defaults to `consumer_comp_db` (D21) when omitted.
2. **Collection** `complaints`; unique upsert key **`Complaint ID`** (also stored as `_id` string).
3. **Helper** `Middleware/Airflow-dags/ccaa/mongo_ingest.py` — stream zip/CSV, batch upsert; no `app.*` imports (D67).
4. **DAG** `ingest_cfpb_all` — `resolve_and_ingest` → `notify_finished` (`ALL_DONE`); conf carries `execution_id` only; reads `config_used.source_filename` (default `complaints.csv.zip`) and optional `batch_size` (default 500).
5. **Callbacks** — extend `report_execution_status` to send `rows_loaded` / `batch_count` / `increment_marker` (API already accepts them, D60).
6. **Out of scope** — workflow seed / MIO bind (#159), Admin DB Ingest UI (#160), AppEndpoint resolution (#161).

## Tests

- DAG file asserts (mirror download).
- `mongo_ingest` unit tests with fake collection (no live Mongo required).
- `status_callback` volume fields.
