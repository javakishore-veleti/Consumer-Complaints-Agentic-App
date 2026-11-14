# M02-0031 (#81) Admin schema and `app_workflows` table with its DAO

Decisions: D43, D48, D52 in `Middleware/ConsumerComplaintsHandsOn/DESIGN.md`; D55 records the naming rules below.

## Goal

Create the admin schema `consumer_comp_admin_db` and the `app_workflows` table (the registry of workflows), with one DAO. No API endpoint, no engine code.

## Naming

- The table is `app_workflows`. In **class names** `Workflows` is shortened to `Wf`: `AppWfDao`, `AppWfCtx`, `AppWfReq`, `AppWfResp`, `AppWfRecord`, `AppWfModel`, `SqlAlchemyAppWfDao`.
- Module names follow the class names: `app_wf_dao.py`, `app_wf_dtos.py`, `sqlalchemy_app_wf_dao.py`.

## Schema

- `config.py`: `SCHEMA_ADMIN = "consumer_comp_admin_db"`, added to `ALL_SCHEMAS`. On SQLite this attaches `consumer_comp_admin_db.sqlite`; on Postgres it is a real schema (`ensure_schemas` already covers both).

## Table `app_workflows`

| Column | Type | Rules |
|---|---|---|
| id | String(36) | primary key, application-generated UUID |
| workflow_name | String(100) | not null, unique |
| engine_type | String(32) | not null, one of `EngineType` |
| engine_workflow_id | String(255) | not null (the Airflow DAG id) |
| config | JSON | **nullable**; NULL means no config (no `{}` stored) |
| enabled | Boolean | not null, default true |
| created_at, updated_at | DateTime(timezone) | not null, UTC |

Migration `0003_create_admin_app_workflows.py`: Alembic Python ops (D23), runs up and down, seeds nothing. The schema itself is created by `alembic/env.py` (`ensure_schemas`) before any migration runs; on SQLite attaching the file creates it.

## Types file

`app/core/common/app_types_constants.py` holds every type list of the app as enums with one parent.

- `AppTypeEnum(str, Enum)`: the parent. No members. One class method, `values()` (list of the string values); callers check `value in EngineType.values()`. There is no `is_valid(value)`: a method taking a bare string breaks the one-object signature rule (D37).
- `EngineType(AppTypeEnum)`: `APACHE_AIRFLOW = "apache_airflow"`, `AWS_STEP_FUNCTIONS = "aws_step_functions"`. M02 runs only `apache_airflow` (D52).
- Later type lists (dataset location types, statuses) are added to this file as further subclasses of `AppTypeEnum`.

## DAO

`AppWfDao(metaclass=SingletonMeta)`. Every method takes one `AppWfCtx` (req and resp, transaction aware like the other DAOs) and returns an integer code. Results go to `ctx.resp.records`.

| Method | Needs | Result |
|---|---|---|
| create | workflow_name, engine_type, engine_workflow_id; optional config, enabled | the new row; CONFLICT on a duplicate name |
| get | id or workflow_name | the row; NOT_FOUND |
| list | optional engine_type, enabled | rows ordered by workflow_name |
| update | id; any of workflow_name, engine_type, engine_workflow_id, config, enabled | the row, `updated_at` set; NOT_FOUND; CONFLICT on a duplicate name |
| delete | id | the deleted row; NOT_FOUND |

Names are trimmed and case sensitive ("Flow" and "flow" are two workflows). `config` must be a JSON object or not given. `CONFLICT` also covers two writers taking the same name at once: the unique constraint decides and the DAO maps `IntegrityError` to `CONFLICT`.

`INVALID_INPUT` for an empty name, a name over 100 characters, an empty `engine_workflow_id`, or an `engine_type` that is not in `EngineType`. Checking against the registered engine classes comes with the engine interface (#83) and the start endpoint (#42).

A config left out means NULL. On update, `config` is changed only when given; clearing it is out of scope.

Files: `dao/app_wf_dao.py`, `dao/impl/sqlalchemy_app_wf_dao.py`, `common/dtos/app_wf_dtos.py`, `AppWfModel` in `dao/impl/models.py`, `get_app_wf_dao()` in `dao/objects_factory.py` (static method style; `init()` is #80). Only `impl/` sees SQLAlchemy.

## Tests

- `tests/test_app_wf_dao.py`: CRUD, every return code above, nested JSON config round trip, NULL config, a shared transaction with rollback, the DAO is a singleton from the factory.
- `test_schema.py`: the new schema and table; migration up, down, up.
- The existing signature, import-contract and singleton tests run over the new code.
- `test_postgres.py`: the same DAO cases when `CCA_TEST_POSTGRES_URL` is set (D33).

## Out of scope

`app_workflows_exec_log` (#82), catalog tables (#86), endpoints, engine classes (#83), factory `init()` (#80).
