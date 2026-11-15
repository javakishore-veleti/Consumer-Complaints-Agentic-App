"""E2E happy-path smoke (M03-0012): start → callbacks → GET /mios/status (no invented status)."""

import httpx
import pytest

from app.core.common.dtos.app_wf_dtos import AppWfCtx
from app.core.common.dtos.mio_dtos import MioCtx, MioReq
from app.core.common.return_codes import SUCCESS
from app.core.dao.objects_factory import DaoObjectsFactory
from app.core.services.impl.airflow_dag_runs_client import AirflowDagRunsClient
from app.core.services.impl.airflow_start_dag_service_impl import AirflowStartDagServiceImpl
from app.core.services.objects_factory import ServicesObjectsFactory

SEEDED_WF = "download_cfpb_all"
SEEDED_MIO = "Customer complaints all 2026"
SECRET = "e2e-smoke-secret"
HEADERS = {"X-Callback-Secret": SECRET}
ALLOWED = ("requested", "started", "completed", "failed")


def _handler(request: httpx.Request) -> httpx.Response:
    if request.url.path == "/auth/token":
        return httpx.Response(201, json={"access_token": "tok"})
    if request.method == "POST" and "/dagRuns" in request.url.path:
        return httpx.Response(200, json={"dag_run_id": "e2e-run-1"})
    return httpx.Response(500)


@pytest.fixture
def mock_airflow(monkeypatch):
    monkeypatch.setenv("CCA_AIRFLOW_API_BASE_URL", "http://airflow.test")
    monkeypatch.setenv("CCA_AIRFLOW_API_USERNAME", "airflow")
    monkeypatch.setenv("CCA_AIRFLOW_API_PASSWORD", "airflow")
    monkeypatch.setenv("CCA_CALLBACK_SECRET", SECRET)
    service = ServicesObjectsFactory.get_airflow_start_dag_service()
    assert isinstance(service, AirflowStartDagServiceImpl)
    service._client = AirflowDagRunsClient(transport=httpx.MockTransport(_handler))


def _mio_entry(client, mio_id: str) -> dict:
    body = client.get("/mios/status").json()
    return next(e for e in body if e["id"] == mio_id)


def test_happy_path_start_callback_mios_status(client, data_dir, mock_airflow):
    listed = AppWfCtx()
    assert DaoObjectsFactory.get_app_wf_dao().list(listed) == SUCCESS
    wf_id = next(r.id for r in listed.resp.records if r.workflow_name == SEEDED_WF)
    mio = MioCtx(req=MioReq(name=SEEDED_MIO))
    assert DaoObjectsFactory.get_mio_dao().get(mio) == SUCCESS
    mio_id = mio.resp.records[0].id

    start = client.post(f"/workflows/{wf_id}/start", json={"mio_id": mio_id})
    assert start.status_code == 202
    execution_id = start.json()["execution_id"]
    assert execution_id

    before = _mio_entry(client, mio_id)
    assert before["latest_ingest"] is not None
    assert before["latest_ingest"]["status"] == "requested"
    assert before["latest_ingest"]["executions"][0]["id"] == execution_id
    assert before["latest_ingest"]["executions"][0]["status"] == "requested"
    assert before["latest_ingest"]["status"] in ALLOWED

    cb = f"/callbacks/workflow-executions/{execution_id}/status"
    started = client.post(cb, json={"status": "started", "engine_run_id": "e2e-run-1"}, headers=HEADERS)
    assert started.status_code == 200
    mid = _mio_entry(client, mio_id)
    assert mid["latest_ingest"]["status"] == "started"
    assert mid["latest_ingest"]["executions"][0]["status"] == "started"
    assert mid["latest_ingest"]["status"] in ALLOWED

    done_resp = client.post(cb, json={"status": "completed", "message": "ok"}, headers=HEADERS)
    assert done_resp.status_code == 200
    done = _mio_entry(client, mio_id)
    assert done["latest_ingest"]["status"] == "completed"
    assert done["latest_ingest"]["executions"][0]["status"] == "completed"
    assert done["latest_ingest"]["status"] in ALLOWED
    # Portal must display these literals from the API — never invent other enums.
    assert done["latest_ingest"]["executions"][0]["status"] in ALLOWED
