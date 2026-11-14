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

from app.core.common.config import ALL_SCHEMAS, PROJECT_ROOT, SCHEMA_ADMIN, SCHEMA_COMPLAINTS
from app.core.common.dtos.app_wf_dtos import AppWfCtx, AppWfReq
from app.core.common.dtos.app_wf_exec_log_dtos import AppWfExecLogCtx, AppWfExecLogReq
from app.core.common.dtos.data_ingest_dtos import DataIngestCtx, DataIngestReq
from app.core.common.dtos.dataset_status_dtos import DatasetStatusCtx, DatasetStatusReq
from app.core.common.return_codes import CONFLICT, INVALID_INPUT, NOT_FOUND, SUCCESS
from app.core.dao.impl import sqlalchemy_app_wf_exec_log_dao as exec_log_impl
from app.core.dao.impl.database import reset_engine
from app.core.dao.objects_factory import DaoObjectsFactory
from app.core.services.objects_factory import ServicesObjectsFactory

URL = os.environ.get("CCA_TEST_POSTGRES_URL")
pytestmark = pytest.mark.skipif(not URL, reason="CCA_TEST_POSTGRES_URL is not set")


@pytest.fixture
def postgres(monkeypatch, tmp_path):
    monkeypatch.setenv("CCA_DB_URL", URL)
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
    assert {"data_ingest_log", "system_datasets"} <= _complaint_tables()
    assert "app_workflows" in _admin_tables()

    command.downgrade(postgres, "base")
    assert not {"data_ingest_log", "system_datasets"} & _complaint_tables()
    assert "app_workflows" not in _admin_tables()

    command.upgrade(postgres, "head")
    assert {"data_ingest_log", "system_datasets"} <= _complaint_tables()
    assert "app_workflows" in _admin_tables()


def test_dataset_status_service_works_on_postgres(postgres):
    command.upgrade(postgres, "head")
    service = ServicesObjectsFactory.get_dataset_status_service()
    ask = DatasetStatusCtx(req=DatasetStatusReq(usecase="download_all"))
    assert service.request(ask) == SUCCESS
    assert service.request(DatasetStatusCtx(req=DatasetStatusReq(usecase="download_all"))) == CONFLICT
    assert service.record(DatasetStatusCtx(req=DatasetStatusReq(usecase="download_all", status="started"))) == SUCCESS
    done = DatasetStatusCtx(req=DatasetStatusReq(usecase="download_all", status="completed"))
    assert service.record(done) == SUCCESS
    rows = DatasetStatusCtx()
    assert service.read(rows) == SUCCESS
    assert {(r.dataset, r.stage): r.status for r in rows.resp.records} == {
        ("3_months", "db_ingest"): "not_started",
        ("3_months", "download"): "not_started",
        ("all", "db_ingest"): "not_started",
        ("all", "download"): "completed",
    }


def test_dao_works_on_postgres(postgres):
    command.upgrade(postgres, "head")
    dao = DaoObjectsFactory.get_data_ingest_dao()
    created = DataIngestCtx(req=DataIngestReq(purpose="download_all"))
    assert dao.create(created) == SUCCESS
    log_id = created.resp.records[0].id
    assert created.resp.records[0].requested_at.tzinfo is not None

    assert dao.update(DataIngestCtx(req=DataIngestReq(id=log_id, status="completed"))) == CONFLICT
    started = DataIngestCtx(req=DataIngestReq(id=log_id, status="started"))
    assert dao.update(started) == SUCCESS
    assert started.resp.records[0].started_at is not None

    listed = DataIngestCtx(req=DataIngestReq(status="started"))
    assert dao.list(listed) == SUCCESS and [r.id for r in listed.resp.records] == [log_id]
    assert dao.delete(DataIngestCtx(req=DataIngestReq(id=log_id))) == SUCCESS


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
    assert dao.list(listed) == SUCCESS and [r.workflow_name for r in listed.resp.records] == ["download_3_months"]
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
