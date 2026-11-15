"""SQLite-first admin store (D76): migrate, start-workflow, callback → rows in .sqlite files."""

import sqlite3

import httpx
from fastapi.testclient import TestClient

from app.api.objects_factory import ApiObjectsFactory
from app.core.common.dtos.app_wf_dtos import AppWfCtx
from app.core.common.dtos.mio_dtos import MioCtx, MioReq
from app.core.common.return_codes import SUCCESS
from app.core.dao.objects_factory import DaoObjectsFactory
from app.core.services.impl.airflow_dag_runs_client import AirflowDagRunsClient
from app.core.services.impl.airflow_start_dag_service_impl import AirflowStartDagServiceImpl
from app.core.services.objects_factory import ServicesObjectsFactory

ADMIN_TABLES = {
    "app_workflows",
    "app_workflows_exec_log",
    "datasets",
    "datasets_location",
    "mios",
    "mios_datasets",
    "mios_ingest_log",
}
SECRET = "sqlite-first-callback-secret"
SEEDED_WF = "download_cfpb_all"
SEEDED_MIO = "Customer complaints all 2026"


def _admin(data_dir):
    return sqlite3.connect(data_dir / "consumer_comp_admin_db.sqlite")


def test_alembic_head_creates_admin_tables_in_sqlite_file(data_dir):
    with _admin(data_dir) as db:
        tables = {r[0] for r in db.execute("select name from sqlite_master where type='table'")}
    assert ADMIN_TABLES <= tables
    assert "system_datasets" not in tables and "data_ingest_log" not in tables


def _mock_airflow(monkeypatch):
    monkeypatch.setenv("CCA_AIRFLOW_API_BASE_URL", "http://airflow.test")
    monkeypatch.setenv("CCA_AIRFLOW_API_USERNAME", "airflow")
    monkeypatch.setenv("CCA_AIRFLOW_API_PASSWORD", "airflow")

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/auth/token":
            return httpx.Response(201, json={"access_token": "tok"})
        if request.method == "POST" and "/dagRuns" in request.url.path:
            return httpx.Response(200, json={"dag_run_id": "sqlite-run-1"})
        return httpx.Response(500)

    service = ServicesObjectsFactory.get_airflow_start_dag_service()
    assert isinstance(service, AirflowStartDagServiceImpl)
    service._client = AirflowDagRunsClient(transport=httpx.MockTransport(handler))


def test_start_workflow_and_callback_persist_to_sqlite_file(data_dir, monkeypatch):
    monkeypatch.setenv("CCA_CALLBACK_SECRET", SECRET)
    _mock_airflow(monkeypatch)
    client = TestClient(ApiObjectsFactory.get_app())

    listed = AppWfCtx()
    assert DaoObjectsFactory.get_app_wf_dao().list(listed) == SUCCESS
    wf_id = next(r.id for r in listed.resp.records if r.workflow_name == SEEDED_WF)

    mio = MioCtx(req=MioReq(name=SEEDED_MIO))
    assert DaoObjectsFactory.get_mio_dao().get(mio) == SUCCESS
    mio_id = mio.resp.records[0].id

    started = client.post(f"/workflows/{wf_id}/start", json={"mio_id": mio_id})
    assert started.status_code == 202
    execution_id = started.json()["execution_id"]

    with _admin(data_dir) as db:
        exec_row = db.execute(
            "select status, engine_run_id, mios_ingest_log_id from app_workflows_exec_log where id = ?",
            (execution_id,),
        ).fetchone()
        assert exec_row is not None
        assert exec_row[0] == "requested"
        assert exec_row[1] == "sqlite-run-1"
        ingest_id = exec_row[2]
        assert ingest_id
        assert db.execute("select status from mios_ingest_log where id = ?", (ingest_id,)).fetchone()[0] == "requested"

    cb = client.post(
        f"/callbacks/workflow-executions/{execution_id}/status",
        json={"status": "started", "engine_run_id": "sqlite-run-1"},
        headers={"X-Callback-Secret": SECRET},
    )
    assert cb.status_code == 200

    with _admin(data_dir) as db:
        assert (
            db.execute("select status from app_workflows_exec_log where id = ?", (execution_id,)).fetchone()[0]
            == "started"
        )
        assert db.execute("select status from mios_ingest_log where id = ?", (ingest_id,)).fetchone()[0] == "started"
