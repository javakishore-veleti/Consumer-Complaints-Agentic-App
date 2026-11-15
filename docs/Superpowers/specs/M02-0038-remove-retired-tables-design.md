# M02-0038 (#88) Remove `system_datasets` and `data_ingest_log` (retired by D47)

Decision: **D74** in `Middleware/ConsumerComplaintsHandsOn/DESIGN.md`. Main tip ends at D73 (#83 WorkflowEngine); this story takes **D74** (not D73).

The user asked for end-to-end completion without clarifying questions; choices below are recorded as D74 so they can be reviewed and reversed.

## Goal

Finish D47: drop the two retired tables and delete every application layer that exists only for them (DAOs, `DatasetStatusService`, `/data-ingest-logs`, DTOs, constants, tests). Keep Alembic history migrations `0001` and `0002`. Do not break catalog, workflow registry, exec/ingest logs, callbacks, or portal paths (`/mios/status`, `/workflows`, start workflow).

## Approach (chosen)

**One drop migration + full code removal in the same story.**

| Option | Trade-off |
|---|---|
| A. Migration only, leave dead code | Leaves broken factories after tables are gone |
| B. Code removal only, leave empty tables | Leaves retired schema in head (fails D47) |
| **C. Migration `0010` drops both; remove all dedicated code** (chosen) | Matches D47 and the acceptance checklist |

## Migration `0010_drop_retired_system_datasets_and_data_ingest_log.py`

- `revision = "0010"`, `down_revision = "0009"`.
- Schema `consumer_comp_db` (`SCHEMA_COMPLAINTS`).
- **upgrade:** drop index `ix_data_ingest_log_purpose_status`, drop `data_ingest_log`, drop `system_datasets`.
- **downgrade:** recreate both tables as in `0001`/`0002` (including the four `system_datasets` seed rows as `not_started`), so down/up is reversible.
- Leave `0001` and `0002` untouched (history).

## Code removed (only serves the retired tables)

| Layer | Remove |
|---|---|
| Models | `DataIngestLogModel`, `SystemDatasetModel` from `dao/impl/models.py` |
| DAOs | `DataIngestDao` / `SqlAlchemyDataIngestDao`, `SystemDatasetsDao` / `SqlAlchemySystemDatasetsDao` and factory getters |
| Service | `DatasetStatusService` / `DatasetStatusServiceImpl` and factory getter |
| Facade | `DataIngestFacade`, impl, task interface, and the four `data_ingest_*` tasks |
| API | `DataIngestApi`, `data_ingest_models.py`, router include in `ApiObjectsFactory` |
| Constants / DTOs | `data_ingest_constants.py`, `dataset_constants.py`, `data_ingest_dtos.py`, `data_ingest_facade_dtos.py`, `system_datasets_dtos.py`, `dataset_status_dtos.py` |

`TransactionDao` stays (used by workflow/MIO status services). D39's example updates to those services.

## Tests

- Delete: `test_data_ingest_dao.py`, `test_data_ingest_api.py`, `test_system_datasets_dao.py`, `test_dataset_status_service.py`.
- Update: `test_schema.py` (tables absent at head; `0010` down/up), `test_postgres.py` (same; drop retired DAO/service cases), `test_singletons.py`, `test_factory_init.py`, `test_callback_secret_api.py` (open portal routes instead of `/data-ingest-logs`).
- Regenerate `openapi.json` (`npm run local:api:openapi`).
- Catalog / workflow / MIO / callback / portal tests stay green unchanged in behavior.

## Docs

- `DESIGN.md`: add D74; mark section 3 retired-table subsections as removed (history only via `0001`/`0002`); update D39 example; set next decision to D75.
- `ARCHITECTURE.md`: stop listing the tables as built; note they were dropped by `0010`.
- `Milestone_02.md`: next decision D75; workflow rows for #88 advanced by `ccaa-milestone-log`.

## Out of scope

Editing history migrations, changing catalog/workflow/MIO schemas, portal UI work, deleting decision rows that mention the old names historically (D14, D40, D41, D47).
