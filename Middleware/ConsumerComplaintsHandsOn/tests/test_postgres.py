"""Migrations and the DAO on a real Postgres. Runs only when CCA_TEST_POSTGRES_URL is set, for example:

    docker run -d --name cca-pg -e POSTGRES_PASSWORD=postgres -p 55432:5432 postgres:16
    CCA_TEST_POSTGRES_URL=postgresql+psycopg://postgres:postgres@localhost:55432/postgres uv run pytest tests/test_postgres.py

CI runs it against a Postgres service container.
"""

import os

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.exc import IntegrityError

from app.core.common.config import ALL_SCHEMAS, PROJECT_ROOT, SCHEMA_ADMIN, SCHEMA_COMPLAINTS
from app.core.common.dtos.app_wf_dtos import AppWfCtx, AppWfReq
from app.core.common.dtos.app_wf_exec_log_dtos import AppWfExecLogCtx, AppWfExecLogReq
from app.core.common.dtos.dataset_dtos import DatasetCtx, DatasetReq
from app.core.common.dtos.dataset_location_dtos import DatasetLocationCtx, DatasetLocationReq
from app.core.common.dtos.mio_dataset_dtos import MioDatasetCtx, MioDatasetReq
from app.core.common.dtos.mio_dtos import MioCtx, MioReq
from app.core.common.dtos.mio_ingest_log_dtos import MioIngestLogCtx, MioIngestLogReq
from app.core.common.dtos.mio_status_dtos import MioStatusCtx, MioStatusReq
from app.core.common.dtos.wf_exec_status_dtos import WfExecStatusCtx, WfExecStatusReq
from app.core.common.dtos.start_wf_dtos import StartWfCtx, StartWfReq
from app.core.common.dtos.wf_list_dtos import WfListCtx, WfListReq
from app.core.common.return_codes import CONFLICT, INVALID_INPUT, NOT_FOUND, SUCCESS
from app.core.dao.impl import sqlalchemy_app_wf_exec_log_dao as exec_log_impl
from app.core.dao.impl import sqlalchemy_mio_ingest_log_dao as ingest_log_impl
from app.core.dao.impl.database import reset_engine
from app.core.dao.objects_factory import DaoObjectsFactory
from app.core.services.objects_factory import ServicesObjectsFactory

URL = os.environ.get("CCA_TEST_POSTGRES_URL")
pytestmark = pytest.mark.skipif(not URL, reason="CCA_TEST_POSTGRES_URL is not set")


@pytest.fixture
def postgres(monkeypatch, tmp_path):
    monkeypatch.setenv("CCA_DB_URL", URL)
    monkeypatch.setenv("CCA_OPERATIONAL_STORE", "postgres")
    monkeypatch.setenv("CCA_DATA_DIR", str(tmp_path))
    reset_engine()
    config = Config(str(PROJECT_ROOT / "alembic.ini"))
    command.downgrade(config, "base")  # start clean
    yield config
    command.downgrade(config, "base")
    reset_engine()


def _complaint_tables():
    engine = create_engine(URL)
    try:
        return set(inspect(engine).get_table_names(schema=SCHEMA_COMPLAINTS))
    finally:
        engine.dispose()


def _admin_tables():
    engine = create_engine(URL)
    try:
        return set(inspect(engine).get_table_names(schema=SCHEMA_ADMIN))
    finally:
        engine.dispose()


def test_upgrade_downgrade_upgrade(postgres):
    command.upgrade(postgres, "head")
    engine = create_engine(URL)
    with engine.connect() as c:
        schemas = {r[0] for r in c.execute(text("select schema_name from information_schema.schemata"))}
    engine.dispose()
    assert set(ALL_SCHEMAS) <= schemas
    assert not {"data_ingest_log", "system_datasets"} & _complaint_tables()
    assert "app_workflows" in _admin_tables()

    command.downgrade(postgres, "0009")
    assert {"data_ingest_log", "system_datasets"} <= _complaint_tables()
    assert "app_workflows" in _admin_tables()

    command.downgrade(postgres, "base")
    assert not {"data_ingest_log", "system_datasets"} & _complaint_tables()
    assert "app_workflows" not in _admin_tables()

    command.upgrade(postgres, "head")
    assert not {"data_ingest_log", "system_datasets"} & _complaint_tables()
    assert "app_workflows" in _admin_tables()


def test_app_wf_dao_works_on_postgres(postgres):
    command.upgrade(postgres, "head")
    assert "app_workflows" in _admin_tables()
    dao = DaoObjectsFactory.get_app_wf_dao()
    config = {"source": {"type": "http", "urls": ["a", "b"]}, "retries": 3, "limit": None}
    created = AppWfCtx(
        req=AppWfReq(workflow_name="download_3_months", engine_type="apache_airflow", engine_workflow_id="dag", config=config)
    )
    assert dao.create(created) == SUCCESS
    row = created.resp.records[0]
    assert row.created_at.tzinfo is not None and row.config == config

    again = AppWfCtx(req=AppWfReq(workflow_name="download_3_months", engine_type="apache_airflow", engine_workflow_id="x"))
    assert dao.create(again) == CONFLICT

    no_config = AppWfCtx(req=AppWfReq(workflow_name="plain", engine_type="aws_step_functions", engine_workflow_id="sm"))
    assert dao.create(no_config) == SUCCESS and no_config.resp.records[0].config is None

    fetched = AppWfCtx(req=AppWfReq(id=row.id))
    assert dao.get(fetched) == SUCCESS and fetched.resp.records[0].config == config
    listed = AppWfCtx(req=AppWfReq(engine_type="apache_airflow"))
    assert dao.list(listed) == SUCCESS and [r.workflow_name for r in listed.resp.records] == [
        "download_3_months",
        "download_cfpb_all",
        "filter_cfpb_3_months",
        "ingest_cfpb_all",
    ]
    assert dao.update(AppWfCtx(req=AppWfReq(id=row.id, enabled=False))) == SUCCESS
    disabled = AppWfCtx(req=AppWfReq(enabled=False))
    assert dao.list(disabled) == SUCCESS and [r.workflow_name for r in disabled.resp.records] == ["download_3_months"]
    assert dao.update(AppWfCtx(req=AppWfReq(id=row.id, workflow_name="plain"))) == CONFLICT
    renamed = AppWfCtx(req=AppWfReq(id=row.id, workflow_name="  renamed  "))
    assert dao.update(renamed) == SUCCESS and renamed.resp.records[0].workflow_name == "renamed"
    assert renamed.resp.records[0].updated_at.tzinfo is not None
    assert dao.delete(AppWfCtx(req=AppWfReq(id=row.id))) == SUCCESS


def test_app_wf_exec_log_dao_works_on_postgres(postgres):
    command.upgrade(postgres, "head")
    assert "app_workflows_exec_log" in _admin_tables()
    workflows = DaoObjectsFactory.get_app_wf_dao()
    logs = DaoObjectsFactory.get_app_wf_exec_log_dao()
    config = {"source": {"type": "http", "urls": ["a", "b"]}, "retries": 3, "limit": None}
    made = AppWfCtx(
        req=AppWfReq(workflow_name="download_3_months", engine_type="apache_airflow", engine_workflow_id="dag", config=config)
    )
    assert workflows.create(made) == SUCCESS
    workflow = made.resp.records[0]

    created = AppWfExecLogCtx(req=AppWfExecLogReq(workflow_id=workflow.id))
    assert logs.create(created) == SUCCESS
    row = created.resp.records[0]
    assert row.status == "requested" and row.config_used == config and row.requested_at.tzinfo is not None
    assert logs.create(AppWfExecLogCtx(req=AppWfExecLogReq(workflow_id="no-such-workflow"))) == NOT_FOUND

    assert logs.update(AppWfExecLogCtx(req=AppWfExecLogReq(id=row.id, status="completed"))) == CONFLICT
    started = AppWfExecLogCtx(req=AppWfExecLogReq(id=row.id, status="started", engine_run_id="run-1"))
    assert logs.update(started) == SUCCESS and started.resp.records[0].started_at is not None
    done = AppWfExecLogCtx(req=AppWfExecLogReq(id=row.id, status="completed"))
    assert logs.update(done) == SUCCESS and done.resp.records[0].finished_at is not None
    assert logs.update(AppWfExecLogCtx(req=AppWfExecLogReq(id=row.id, status="failed"))) == CONFLICT

    # No foreign key: the row survives the workflow being renamed and then deleted.
    assert workflows.update(AppWfCtx(req=AppWfReq(id=workflow.id, workflow_name="renamed"))) == SUCCESS
    assert workflows.delete(AppWfCtx(req=AppWfReq(id=workflow.id))) == SUCCESS
    fetched = AppWfExecLogCtx(req=AppWfExecLogReq(id=row.id))
    assert logs.get(fetched) == SUCCESS
    assert (fetched.resp.records[0].workflow_name, fetched.resp.records[0].config_used) == ("download_3_months", config)

    listed = AppWfExecLogCtx(req=AppWfExecLogReq(workflow_id=workflow.id, status="completed"))
    assert logs.list(listed) == SUCCESS and [r.id for r in listed.resp.records] == [row.id]

    command.downgrade(postgres, "0003")
    assert "app_workflows_exec_log" not in _admin_tables()
    command.upgrade(postgres, "head")
    assert "app_workflows_exec_log" in _admin_tables()


def test_app_wf_exec_log_rival_callback_does_not_overwrite_on_postgres(postgres, monkeypatch):
    # Postgres runs at READ COMMITTED: both callbacks read "started". _now() runs after update's read and before its
    # write, so a rival that commits inside it is the race; the conditional write must lose cleanly.
    command.upgrade(postgres, "head")
    made = AppWfCtx(req=AppWfReq(workflow_name="w", engine_type="apache_airflow", engine_workflow_id="dag"))
    assert DaoObjectsFactory.get_app_wf_dao().create(made) == SUCCESS
    logs = DaoObjectsFactory.get_app_wf_exec_log_dao()
    created = AppWfExecLogCtx(req=AppWfExecLogReq(workflow_id=made.resp.records[0].id))
    assert logs.create(created) == SUCCESS
    row_id = created.resp.records[0].id
    assert logs.update(AppWfExecLogCtx(req=AppWfExecLogReq(id=row_id, status="started"))) == SUCCESS

    real_now = exec_log_impl._now
    raced = []

    def now_after_a_rival_wins():
        if not raced:
            raced.append(True)
            rival = AppWfExecLogCtx(req=AppWfExecLogReq(id=row_id, status="failed", message="rival"))
            assert logs.update(rival) == SUCCESS
        return real_now()

    monkeypatch.setattr(exec_log_impl, "_now", now_after_a_rival_wins)
    loser = AppWfExecLogCtx(req=AppWfExecLogReq(id=row_id, status="completed", message="loser"))
    assert logs.update(loser) == CONFLICT

    stored = AppWfExecLogCtx(req=AppWfExecLogReq(id=row_id))
    assert logs.get(stored) == SUCCESS
    assert (stored.resp.records[0].status, stored.resp.records[0].message) == ("failed", "rival")
    assert logs.list(AppWfExecLogCtx(req=AppWfExecLogReq(limit=-1))) == INVALID_INPUT


def test_catalog_works_on_postgres(postgres):
    command.upgrade(postgres, "head")
    assert {
        "datasets",
        "datasets_location",
        "mios",
        "mios_datasets",
        "mios_workflows",
        "app_endpoints",
    } <= _admin_tables()
    engine = create_engine(URL)
    with engine.connect() as c:
        seeded = c.execute(text(f"select count(*) from {SCHEMA_ADMIN}.mios")).scalar()
        bindings = c.execute(text(f"select count(*) from {SCHEMA_ADMIN}.mios_workflows")).scalar()
        endpoints = c.execute(text(f"select count(*) from {SCHEMA_ADMIN}.app_endpoints")).scalar()
    assert seeded == 5  # four month MIOs + All (0011 / D84)
    assert bindings == 3
    assert endpoints == 2  # source + ingest AppEndpoints (0012 / 0014)

    datasets = DaoObjectsFactory.get_dataset_dao()
    locations = DaoObjectsFactory.get_dataset_location_dao()
    mios = DaoObjectsFactory.get_mio_dao()
    links = DaoObjectsFactory.get_mio_dataset_dao()

    made = DatasetCtx(req=DatasetReq(name="t_ds", code="T1"))
    assert datasets.create(made) == SUCCESS
    dataset = made.resp.records[0]
    assert dataset.created_at.tzinfo is not None
    assert datasets.create(DatasetCtx(req=DatasetReq(name="t_ds", code="T9"))) == CONFLICT
    assert datasets.create(DatasetCtx(req=DatasetReq(name="t_other", code="T1"))) == CONFLICT
    assert datasets.create(DatasetCtx(req=DatasetReq(name="t_other", code="CFPB"))) == CONFLICT  # the seed's code

    http_req = DatasetLocationReq(dataset_id=dataset.id, location_type="http", path="https://x")
    http = DatasetLocationCtx(req=http_req)
    env = DatasetLocationCtx(
        req=DatasetLocationReq(dataset_id=dataset.id, location_type="local", local_env_var_name="LOCAL_DATA_PATH_T1")
    )
    assert locations.create(http) == SUCCESS and locations.create(env) == SUCCESS
    assert locations.create(DatasetLocationCtx(req=http_req)) == CONFLICT
    both = DatasetLocationReq(
        dataset_id=dataset.id, location_type="local", path="/a", local_env_var_name="LOCAL_DATA_PATH_T1"
    )
    assert locations.create(DatasetLocationCtx(req=both)) == INVALID_INPUT
    listed = DatasetLocationCtx(req=DatasetLocationReq(dataset_id=dataset.id))
    assert locations.list(listed) == SUCCESS
    assert [r.location_type for r in listed.resp.records] == ["http", "local"]  # the same order as on SQLite

    # The check constraint holds in the database itself, not only in the DAO.
    with pytest.raises(IntegrityError, match="ck_datasets_location_path_xor_env"):
        with engine.begin() as c:
            c.execute(
                text(
                    f"insert into {SCHEMA_ADMIN}.datasets_location"
                    " (id, dataset_id, location_type, path, local_env_var_name, created_at, updated_at)"
                    " values ('x', :d, 'local', 'p', 'E', now(), now())"
                ),
                {"d": dataset.id},
            )
    engine.dispose()

    mio = MioCtx(req=MioReq(name="t_mio"))
    assert mios.create(mio) == SUCCESS
    mio_id = mio.resp.records[0].id
    link = MioDatasetCtx(
        req=MioDatasetReq(mio_id=mio_id, dataset_id=dataset.id, dataset_location_id=http.resp.records[0].id)
    )
    assert links.create(link) == SUCCESS
    assert links.create(MioDatasetCtx(req=link.req)) == CONFLICT
    assert mios.delete(MioCtx(req=MioReq(id=mio_id))) == CONFLICT
    assert datasets.delete(DatasetCtx(req=DatasetReq(id=dataset.id))) == CONFLICT
    assert links.delete(MioDatasetCtx(req=MioDatasetReq(id=link.resp.records[0].id))) == SUCCESS
    assert mios.delete(MioCtx(req=MioReq(id=mio_id))) == SUCCESS

    command.downgrade(postgres, "0004")
    assert not {
        "datasets",
        "datasets_location",
        "mios",
        "mios_datasets",
        "mios_workflows",
        "app_endpoints",
    } & _admin_tables()
    command.upgrade(postgres, "head")
    assert {
        "datasets",
        "datasets_location",
        "mios",
        "mios_datasets",
        "mios_workflows",
        "app_endpoints",
    } <= _admin_tables()


def test_mio_ingest_log_works_on_postgres(postgres, monkeypatch):
    command.upgrade(postgres, "head")
    assert "mios_ingest_log" in _admin_tables()
    ingests = DaoObjectsFactory.get_mio_ingest_log_dao()
    executions = DaoObjectsFactory.get_app_wf_exec_log_dao()
    mio = MioCtx(req=MioReq(name="t_ingest_mio"))
    assert DaoObjectsFactory.get_mio_dao().create(mio) == SUCCESS
    mio_id = mio.resp.records[0].id

    created = MioIngestLogCtx(req=MioIngestLogReq(mio_id=mio_id, rows_loaded=5_000_000_000, increment_marker="m"))
    assert ingests.create(created) == SUCCESS
    row = created.resp.records[0]
    assert row.status == "requested" and row.requested_at.tzinfo is not None
    assert row.rows_loaded == 5_000_000_000  # BigInteger: above the 32-bit range
    assert ingests.create(MioIngestLogCtx(req=MioIngestLogReq(mio_id="no-such-mio"))) == NOT_FOUND
    assert ingests.create(MioIngestLogCtx(req=MioIngestLogReq(mio_id=mio_id, batch_count=-1))) == INVALID_INPUT
    assert ingests.update(MioIngestLogCtx(req=MioIngestLogReq(id=row.id, status="completed"))) == CONFLICT
    assert ingests.update(MioIngestLogCtx(req=MioIngestLogReq(id=row.id, status="started"))) == SUCCESS

    # Postgres runs at READ COMMITTED: a rival that commits between update's read and its write must win cleanly.
    real_now = ingest_log_impl._now
    raced = []

    def now_after_a_rival_wins():
        if not raced:
            raced.append(True)
            rival = MioIngestLogCtx(req=MioIngestLogReq(id=row.id, status="failed", message="rival"))
            assert ingests.update(rival) == SUCCESS
        return real_now()

    monkeypatch.setattr(ingest_log_impl, "_now", now_after_a_rival_wins)
    loser = MioIngestLogCtx(req=MioIngestLogReq(id=row.id, status="completed", message="loser"))
    assert ingests.update(loser) == CONFLICT
    monkeypatch.setattr(ingest_log_impl, "_now", real_now)
    stored = MioIngestLogCtx(req=MioIngestLogReq(id=row.id))
    assert ingests.get(stored) == SUCCESS
    assert (stored.resp.records[0].status, stored.resp.records[0].message) == ("failed", "rival")
    late = MioIngestLogCtx(req=MioIngestLogReq(id=row.id, batch_count=3))  # a note on a final row
    assert ingests.update(late) == SUCCESS and late.resp.records[0].batch_count == 3
    listed = MioIngestLogCtx(req=MioIngestLogReq(mio_id=mio_id, status="failed"))
    assert ingests.list(listed) == SUCCESS and [r.id for r in listed.resp.records] == [row.id]

    made = AppWfCtx(req=AppWfReq(workflow_name="w", engine_type="apache_airflow", engine_workflow_id="dag"))
    assert DaoObjectsFactory.get_app_wf_dao().create(made) == SUCCESS
    workflow_id = made.resp.records[0].id
    ids = []
    for _ in range(2):
        execution = AppWfExecLogCtx(req=AppWfExecLogReq(workflow_id=workflow_id, mios_ingest_log_id=row.id))
        assert executions.create(execution) == SUCCESS
        ids.append(execution.resp.records[0].id)
    unknown = AppWfExecLogCtx(req=AppWfExecLogReq(workflow_id=workflow_id, mios_ingest_log_id="no-such-ingest"))
    assert executions.create(unknown) == NOT_FOUND
    served = AppWfExecLogCtx(req=AppWfExecLogReq(mios_ingest_log_id=row.id))
    assert executions.list(served) == SUCCESS and sorted(r.id for r in served.resp.records) == sorted(ids)

    def exec_log_columns():
        engine = create_engine(URL)
        try:
            return {c["name"] for c in inspect(engine).get_columns("app_workflows_exec_log", schema=SCHEMA_ADMIN)}
        finally:
            engine.dispose()

    command.downgrade(postgres, "0006")
    assert "mios_ingest_log" not in _admin_tables()
    assert "mios_ingest_log_id" not in exec_log_columns()
    command.upgrade(postgres, "head")
    assert "mios_ingest_log" in _admin_tables()
    assert "mios_ingest_log_id" in exec_log_columns()


def test_wf_exec_status_service_works_on_postgres(postgres):
    command.upgrade(postgres, "head")
    mio = MioCtx(req=MioReq(name="t_status_mio"))
    assert DaoObjectsFactory.get_mio_dao().create(mio) == SUCCESS
    ingest = MioIngestLogCtx(req=MioIngestLogReq(mio_id=mio.resp.records[0].id))
    assert DaoObjectsFactory.get_mio_ingest_log_dao().create(ingest) == SUCCESS
    ingest_id = ingest.resp.records[0].id
    made = AppWfCtx(req=AppWfReq(workflow_name="w", engine_type="apache_airflow", engine_workflow_id="dag"))
    assert DaoObjectsFactory.get_app_wf_dao().create(made) == SUCCESS
    ids = []
    for _ in range(2):
        req = AppWfExecLogReq(workflow_id=made.resp.records[0].id, mios_ingest_log_id=ingest_id)
        execution = AppWfExecLogCtx(req=req)
        assert DaoObjectsFactory.get_app_wf_exec_log_dao().create(execution) == SUCCESS
        ids.append(execution.resp.records[0].id)

    def report(req):
        ctx = WfExecStatusCtx(req=req)
        ServicesObjectsFactory.get_wf_exec_status_service().record(ctx)
        return ctx.resp

    for execution_id in ids:
        assert report(WfExecStatusReq(execution_id=execution_id, status="started")).code == SUCCESS
    first = report(WfExecStatusReq(execution_id=ids[0], status="completed", rows_loaded=5_000_000_000))
    assert (first.code, first.ingest.status, first.ingest.rows_loaded) == (SUCCESS, "started", 5_000_000_000)
    assert report(WfExecStatusReq(execution_id=ids[0], status="failed")).code == CONFLICT
    last = report(WfExecStatusReq(execution_id=ids[1], status="completed", message="done"))
    assert (last.code, last.ingest.status, last.ingest.message) == (SUCCESS, "completed", "done")
    again = report(WfExecStatusReq(execution_id=ids[1], status="completed"))
    assert (again.code, again.ingest) == (SUCCESS, last.ingest)
    assert report(WfExecStatusReq(execution_id=ids[1], status="completed", batch_count=-1)).code == INVALID_INPUT
    assert report(WfExecStatusReq(execution_id="no-such-execution", status="started")).code == NOT_FOUND


def test_mio_status_service_works_on_postgres(postgres):
    command.upgrade(postgres, "head")
    mio = MioCtx(req=MioReq(name="t_read_status_mio"))
    assert DaoObjectsFactory.get_mio_dao().create(mio) == SUCCESS
    mio_id = mio.resp.records[0].id
    ingest = MioIngestLogCtx(req=MioIngestLogReq(mio_id=mio_id, message="live"))
    assert DaoObjectsFactory.get_mio_ingest_log_dao().create(ingest) == SUCCESS
    made = AppWfCtx(req=AppWfReq(workflow_name="w_read", engine_type="apache_airflow", engine_workflow_id="dag"))
    assert DaoObjectsFactory.get_app_wf_dao().create(made) == SUCCESS
    execution = AppWfExecLogCtx(
        req=AppWfExecLogReq(workflow_id=made.resp.records[0].id, mios_ingest_log_id=ingest.resp.records[0].id)
    )
    assert DaoObjectsFactory.get_app_wf_exec_log_dao().create(execution) == SUCCESS

    ctx = MioStatusCtx(req=MioStatusReq(mio_id=mio_id))
    assert ServicesObjectsFactory.get_mio_status_service().read(ctx) == SUCCESS
    assert len(ctx.resp.entries) == 1
    entry = ctx.resp.entries[0]
    assert entry.id == mio_id
    assert entry.latest_ingest is not None
    assert entry.latest_ingest.message == "live"
    assert [x.id for x in entry.latest_ingest.executions] == [execution.resp.records[0].id]
    missing = MioStatusCtx(req=MioStatusReq(mio_id="missing"))
    assert ServicesObjectsFactory.get_mio_status_service().read(missing) == NOT_FOUND


def test_wf_list_service_works_on_postgres(postgres):
    command.upgrade(postgres, "head")
    made = AppWfCtx(
        req=AppWfReq(
            workflow_name="t_pg_list",
            engine_type="apache_airflow",
            engine_workflow_id="dag",
            config={"hide": True},
        )
    )
    assert DaoObjectsFactory.get_app_wf_dao().create(made) == SUCCESS
    ctx = WfListCtx(req=WfListReq())
    assert ServicesObjectsFactory.get_wf_list_service().list(ctx) == SUCCESS
    assert [e.workflow_name for e in ctx.resp.entries] == [
        "download_cfpb_all",
        "filter_cfpb_3_months",
        "ingest_cfpb_all",
        "t_pg_list",
    ]
    assert all(not hasattr(e, "config") for e in ctx.resp.entries)


def test_start_wf_service_works_on_postgres(postgres):
    command.upgrade(postgres, "head")
    listed = AppWfCtx()
    assert DaoObjectsFactory.get_app_wf_dao().list(listed) == SUCCESS
    wf_id = next(r.id for r in listed.resp.records if r.workflow_name == "download_cfpb_all")
    ctx = StartWfCtx(req=StartWfReq(workflow_id=wf_id))
    assert ServicesObjectsFactory.get_start_wf_service().start(ctx) == SUCCESS
    assert ctx.resp.execution_id
    got = AppWfExecLogCtx(req=AppWfExecLogReq(id=ctx.resp.execution_id))
    assert DaoObjectsFactory.get_app_wf_exec_log_dao().get(got) == SUCCESS
    assert got.resp.records[0].status == "requested"


def test_start_workflow_and_callback_persist_on_postgres(postgres, monkeypatch):
    """D77 smoke: HTTP start + callback leave rows readable in the Postgres admin schema."""
    import httpx
    from fastapi.testclient import TestClient

    from app.api.objects_factory import ApiObjectsFactory
    from app.core.services.impl.airflow_dag_runs_client import AirflowDagRunsClient
    from app.core.services.impl.airflow_start_dag_service_impl import AirflowStartDagServiceImpl

    command.upgrade(postgres, "head")
    secret = "postgres-via-env-callback-secret"
    monkeypatch.setenv("CCA_CALLBACK_SECRET", secret)
    monkeypatch.setenv("CCA_AIRFLOW_API_BASE_URL", "http://airflow.test")
    monkeypatch.setenv("CCA_AIRFLOW_API_USERNAME", "airflow")
    monkeypatch.setenv("CCA_AIRFLOW_API_PASSWORD", "airflow")

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/auth/token":
            return httpx.Response(201, json={"access_token": "tok"})
        if request.method == "POST" and "/dagRuns" in request.url.path:
            return httpx.Response(200, json={"dag_run_id": "pg-run-1"})
        return httpx.Response(500)

    service = ServicesObjectsFactory.get_airflow_start_dag_service()
    assert isinstance(service, AirflowStartDagServiceImpl)
    service._client = AirflowDagRunsClient(transport=httpx.MockTransport(handler))

    client = TestClient(ApiObjectsFactory.get_app())
    listed = AppWfCtx()
    assert DaoObjectsFactory.get_app_wf_dao().list(listed) == SUCCESS
    wf_id = next(r.id for r in listed.resp.records if r.workflow_name == "download_cfpb_all")
    mio = MioCtx(req=MioReq(name="Customer complaints all 2026"))
    assert DaoObjectsFactory.get_mio_dao().get(mio) == SUCCESS
    mio_id = mio.resp.records[0].id

    started = client.post(f"/workflows/{wf_id}/start", json={"mio_id": mio_id})
    assert started.status_code == 202
    execution_id = started.json()["execution_id"]

    engine = create_engine(URL)
    with engine.connect() as c:
        exec_row = c.execute(
            text(
                f"select status, engine_run_id, mios_ingest_log_id from {SCHEMA_ADMIN}.app_workflows_exec_log"
                " where id = :id"
            ),
            {"id": execution_id},
        ).fetchone()
        assert exec_row is not None
        assert exec_row[0] == "requested"
        assert exec_row[1] == "pg-run-1"
        ingest_id = exec_row[2]
        assert ingest_id
        assert (
            c.execute(
                text(f"select status from {SCHEMA_ADMIN}.mios_ingest_log where id = :id"),
                {"id": ingest_id},
            ).scalar()
            == "requested"
        )

    cb = client.post(
        f"/callbacks/workflow-executions/{execution_id}/status",
        json={"status": "started", "engine_run_id": "pg-run-1"},
        headers={"X-Callback-Secret": secret},
    )
    assert cb.status_code == 200

    with engine.connect() as c:
        assert (
            c.execute(
                text(f"select status from {SCHEMA_ADMIN}.app_workflows_exec_log where id = :id"),
                {"id": execution_id},
            ).scalar()
            == "started"
        )
        assert (
            c.execute(
                text(f"select status from {SCHEMA_ADMIN}.mios_ingest_log where id = :id"),
                {"id": ingest_id},
            ).scalar()
            == "started"
        )
    engine.dispose()
