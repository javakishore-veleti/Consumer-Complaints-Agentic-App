# M02-0036 (#86) Catalog tables: datasets, datasets_location, mios and mios_datasets, with the seed MIOs

Decisions: D7, D22, D23, D26, D37, D45, D48, D49, D55, D56 and D57 in `Middleware/ConsumerComplaintsHandsOn/DESIGN.md`.

## Goal

Four catalog tables in the admin schema with one DAO each, and a seed of one dataset, its locations and four MIOs. No endpoint, no workflow code, no portal.

## What the catalog means

- A **dataset** is a thing that can be downloaded and ingested. A **location** says where one dataset is available. A **MIO** (managed information object) is attached to datasets, and to one chosen location of each, through `mios_datasets`.
- **Many MIOs can reuse the same dataset and the same location** (the product allows it). A MIO's `name` and `description` are labels for people: **no code anywhere (DAOs, seeds, tests, later workflows) reads them to choose a dataset, location or time window.** `mios_datasets` is the only link between a MIO and its data. Where a time window such as "3 months" would be stored is not modeled here (open item in `DESIGN.md`).

## Naming

`Wf` is only for workflows (D55), so these are `DatasetDao`, `DatasetLocationDao`, `MioDao`, `MioDatasetDao`; `DatasetCtx`/`Req`/`Resp`/`Record`, `DatasetLocationCtx`/..., `MioCtx`/..., `MioDatasetCtx`/...; models `DatasetModel`, `DatasetLocationModel`, `MioModel`, `MioDatasetModel`; implementations `SqlAlchemyDatasetDao`, `SqlAlchemyDatasetLocationDao`, `SqlAlchemyMioDao`, `SqlAlchemyMioDatasetDao`. Modules follow the class names: `dataset_dtos.py`, `dataset_location_dtos.py`, `mio_dtos.py`, `mio_dataset_dtos.py` in `common/dtos/`; `dataset_dao.py` and the other three in `dao/`; `sqlalchemy_dataset_dao.py` and the other three in `dao/impl/`.

## Tables (migration `0005_create_admin_catalog.py`; schema `consumer_comp_admin_db`)

| Table | Column | Type | Rules |
|---|---|---|---|
| `datasets` | id | String(36) | primary key, application-generated UUID |
| | name | String(100) | not null, unique (`uq_datasets_name`), trimmed, case sensitive |
| | code | String(15) | not null, unique (`uq_datasets_code`), only `A-Z` and `0-9`, 1 to 15 characters; builds the local env var name |
| | description | Text | nullable |
| | created_at, updated_at | DateTime(timezone) | not null, UTC |
| `datasets_location` | id | String(36) | primary key |
| | dataset_id | String(36) | not null, indexed, no foreign key |
| | location_type | String(32) | not null, one of `DatasetLocationType` |
| | path | String(1000) | nullable; the literal path or URL; see the rule below |
| | local_env_var_name | String(64) | nullable; only for `local`; see the rule below |
| | credentials_ref | String(100) | nullable; a name, never a value |
| | description | Text | nullable |
| | created_at, updated_at | DateTime(timezone) | not null, UTC |
| `mios` | id | String(36) | primary key |
| | name | String(100) | not null, unique (`uq_mios_name`), trimmed, case sensitive |
| | description | Text | nullable |
| | created_at, updated_at | DateTime(timezone) | not null, UTC |
| `mios_datasets` | id | String(36) | primary key |
| | mio_id | String(36) | not null, indexed, no foreign key |
| | dataset_id | String(36) | not null, no foreign key |
| | dataset_location_id | String(36) | not null, no foreign key: the chosen location |
| | created_at | DateTime(timezone) | not null, UTC |

Constraints: `datasets_location` is unique on (`dataset_id`, `location_type`, `path`) and on (`dataset_id`, `local_env_var_name`) (`uq_datasets_location_*`); `mios_datasets` is unique on (`mio_id`, `dataset_id`) (`uq_mios_datasets_mio_dataset`): one chosen location per dataset per MIO, while any number of MIOs may point to the same dataset. A check constraint `ck_datasets_location_path_xor_env` on `datasets_location`: exactly one of `path` and `local_env_var_name` is not NULL.

`mios` has no config or window column: the window of a MIO is not part of this story.

## Location rules

- `DatasetLocationType(AppTypeEnum)` in `app_types_constants.py`: `local`, `http`, `github`, `s3`, `azure_blob`, `gcs`, `google_drive`, `ftp` (the list of D49). The DAO rejects any other value with `INVALID_INPUT`.
- **`path` and `local_env_var_name` are mutually exclusive, and exactly one is given.** `local_env_var_name` is the **name** of an environment variable the download reads when it runs (D51), so each environment (a laptop, an EC2 instance, a Kubernetes pod with the same EFS mounted on a different path) sets its own value; `path` is a fixed string. Both given, or neither, is `INVALID_INPUT`; the check constraint rejects it in the database too.
- `local_env_var_name` is only allowed for the type `local`. Every other type needs `path`.
- The name must be exactly `LOCAL_DATA_PATH_` followed by the `code` of the location's dataset (for example `LOCAL_DATA_PATH_CFPB`); anything else is `INVALID_INPUT`. The code is at most 15 characters, so the name is at most 31 characters. Only the name is stored, never a value.
- `path` is not empty and up to 1000 characters after trimming.
- `credentials_ref` holds a name only: letters, digits, `_`, `.` and `-`, 1 to 100 characters, no spaces, no `=` and no `://`. Anything else (for example a pasted key or URL) is `INVALID_INPUT`.
- On update, giving `path` sets it and clears `local_env_var_name`; giving `local_env_var_name` sets it and clears `path`; giving both is `INVALID_INPUT`. A change of `location_type` is checked against the resulting row.

## DAO rules (D56 style: no database foreign keys)

SQLite here does not enforce foreign keys and Postgres does, so the integrity rules are kept by the DAOs, in the same transaction, and behave the same on both. Every DAO has `create`, `get`, `list`, `update` and `delete`; every method takes one ctx and returns an integer code (D5, D22, D37), results go to `ctx.resp.records`, and a ctx with a shared transaction joins it.

| DAO | get | list | create / update checks |
|---|---|---|---|
| `DatasetDao` | `id` or `name` (id wins) | ordered by name | name and code valid; a duplicate name or code is `CONFLICT` (also when two writers race: the unique constraint decides); the code of a dataset that has a `local` location with an env var name cannot be changed (`CONFLICT`) |
| `DatasetLocationDao` | `id` | filters `dataset_id`, `location_type`; ordered by `location_type`, rows with a path before rows without, `path`, `id` (SQLite and Postgres sort NULLs differently, so the order is spelled out) | the dataset must exist (`NOT_FOUND`); location rules above; a duplicate is `CONFLICT` |
| `MioDao` | `id` or `name` (id wins) | ordered by name | name valid; duplicate name is `CONFLICT` |
| `MioDatasetDao` | `id` | filters `mio_id`, `dataset_id`; ordered by `created_at`, `id` | the MIO, dataset and location must exist (`NOT_FOUND`); the location must belong to that dataset (`INVALID_INPUT`); a second link of the same MIO and dataset is `CONFLICT`; update may change only `dataset_location_id` |

Delete: a dataset that still has locations or is linked from `mios_datasets`, a MIO that still has links, and a location that a `mios_datasets` row uses are each `CONFLICT`; the deleted row is returned. Child DAOs read the parent table classes (`DatasetModel`, `MioModel`, `DatasetLocationModel`) for these checks, the same exception to D7 as D56. A delete racing a create could leave an orphan (no foreign key); accepted for the MVP.

All four are singletons (`SingletonMeta`, D26), handed out by `dao/objects_factory.py` as `get_dataset_dao()`, `get_dataset_location_dao()`, `get_mio_dao()` and `get_mio_dataset_dao()` (D45). Only `dao/impl` imports SQLAlchemy.

## Seed (migration `0006_seed_admin_catalog.py`)

Fixed ids (UUIDs written in the migration), so a downgrade removes exactly these rows. Only data that is the same in every environment is seeded: no machine path.

| Table | Rows |
|---|---|
| `datasets` | name `cfpb_consumer_complaints`, code `CFPB`, description "The full CFPB Consumer Complaint Database file" |
| `datasets_location` | (1) `http`, `https://files.consumerfinance.gov/ccdb/complaints.csv.zip`, no credentials, no env var name. (2) `local`, no `path`, `local_env_var_name` = `LOCAL_DATA_PATH_CFPB`: where the download puts the file is set per environment |
| `mios` | "Customer complaints 3 months 2026", "Customer complaints 6 months 2026", "Customer complaints 9 months 2026", "Customer complaints 12 months 2026"; description of each: "A label only. The data is what mios_datasets links." |
| `mios_datasets` | each of the four MIOs linked to `cfpb_consumer_complaints` with the `http` location |

The four MIOs are identical in data: the labels carry no meaning (see above). Seeded rows are ordinary rows; they are changed through the DAOs.

## Tests

- One test file per DAO (`tests/test_dataset_dao.py`, `tests/test_dataset_location_dao.py`, `tests/test_mio_dao.py`, `tests/test_mio_dataset_dao.py`): create, get, list (filters and order), update, delete; every rule above (validation, duplicates, `NOT_FOUND`, `CONFLICT` on delete, a location of another dataset, the path / env var name exclusivity with each combination, the name shape, a bad `credentials_ref`, a code that cannot change while an env var name uses it); many MIOs linked to one dataset and one location; a shared transaction with rollback.
- `tests/test_schema.py`: the four tables, columns, constraints (including the check constraint and the unique constraints), no foreign keys; migrations `0005` and `0006` up, down and up; the seed rows are present after `upgrade` and gone after `downgrade` to `0005`, and the tables are gone after `downgrade` to `0004`.
- `tests/test_catalog_flow.py`: a MIO renamed to any text changes nothing about the dataset or location it links, and two MIOs can link the same dataset and location.
- `tests/test_singletons.py`: the four factory methods and classes. `tests/test_app_types_constants.py`: `DatasetLocationType`. `tests/test_postgres.py`: the whole flow on Postgres when `CCA_TEST_POSTGRES_URL` is set (D33), including the check and unique constraints.

## Out of scope

The portal and any endpoint, the link between a workflow and a MIO, a time window for a MIO, resolving the env var (the download workflow does that when it runs), `mios_ingest_log` (#87), removing `system_datasets` and `data_ingest_log` (#88).
