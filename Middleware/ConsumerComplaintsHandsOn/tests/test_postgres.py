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

from app.core.common.config import ALL_SCHEMAS, PROJECT_ROOT, SCHEMA_COMPLAINTS
from app.core.common.dtos.data_ingest_dtos import DataIngestCtx, DataIngestReq
from app.core.common.dtos.dataset_status_dtos import DatasetStatusCtx, DatasetStatusReq
from app.core.common.return_codes import CONFLICT, SUCCESS
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


def test_upgrade_downgrade_upgrade(postgres):
    command.upgrade(postgres, "head")
    engine = create_engine(URL)
    with engine.connect() as c:
        schemas = {r[0] for r in c.execute(text("select schema_name from information_schema.schemata"))}
    engine.dispose()
    assert set(ALL_SCHEMAS) <= schemas
    assert {"data_ingest_log", "system_datasets"} <= _complaint_tables()

    command.downgrade(postgres, "base")
    assert not {"data_ingest_log", "system_datasets"} & _complaint_tables()

    command.upgrade(postgres, "head")
    assert {"data_ingest_log", "system_datasets"} <= _complaint_tables()


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
