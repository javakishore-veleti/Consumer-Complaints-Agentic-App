"""POST /workflows/{id}/start through HTTP (D68)."""

import httpx
import pytest

from app.core.common.dtos.app_wf_dtos import AppWfCtx
from app.core.common.dtos.app_wf_exec_log_dtos import AppWfExecLogCtx, AppWfExecLogReq
from app.core.common.return_codes import SUCCESS
from app.core.dao.objects_factory import DaoObjectsFactory
from app.core.services.impl.airflow_dag_runs_client import AirflowDagRunsClient
from app.core.services.impl.airflow_start_dag_service_impl import AirflowStartDagServiceImpl
from app.core.services.objects_factory import ServicesObjectsFactory

SEEDED = "download_cfpb_all"


def _handler(request: httpx.Request) -> httpx.Response:
    if request.url.path == "/auth/token":
        return httpx.Response(201, json={"access_token": "tok"})
    if request.method == "POST" and "/dagRuns" in request.url.path:
        return httpx.Response(200, json={"dag_run_id": "run-api-1"})
    return httpx.Response(500)


def _fail(request: httpx.Request) -> httpx.Response:
    if request.url.path == "/auth/token":
        return httpx.Response(201, json={"access_token": "tok"})
    return httpx.Response(503, json={"detail": "down"})


@pytest.fixture
def seeded_wf_id(data_dir):
    listed = AppWfCtx()
    assert DaoObjectsFactory.get_app_wf_dao().list(listed) == SUCCESS
    return next(r.id for r in listed.resp.records if r.workflow_name == SEEDED)


@pytest.fixture
def mock_airflow(monkeypatch):
    monkeypatch.setenv("CCA_AIRFLOW_API_BASE_URL", "http://airflow.test")
    monkeypatch.setenv("CCA_AIRFLOW_API_USERNAME", "airflow")
    monkeypatch.setenv("CCA_AIRFLOW_API_PASSWORD", "airflow")
    service = ServicesObjectsFactory.get_airflow_start_dag_service()
    assert isinstance(service, AirflowStartDagServiceImpl)
    service._client = AirflowDagRunsClient(transport=httpx.MockTransport(_handler))


def test_start_returns_202_with_execution_id(client, seeded_wf_id, mock_airflow):
    response = client.post(f"/workflows/{seeded_wf_id}/start", json={})
    assert response.status_code == 202
    body = response.json()
    assert body["execution_id"]
    got = AppWfExecLogCtx(req=AppWfExecLogReq(id=body["execution_id"]))
    assert DaoObjectsFactory.get_app_wf_exec_log_dao().get(got) == SUCCESS
    assert got.resp.records[0].engine_run_id == "run-api-1"


def test_unknown_workflow_is_422(client, mock_airflow):
    response = client.post("/workflows/no-such/start", json={})
    assert response.status_code == 422
    assert response.json()["detail"] == "invalid request"


@pytest.mark.parametrize("secret", [None, "any-value"])
def test_no_callback_secret_is_required(client, seeded_wf_id, mock_airflow, monkeypatch, secret):
    if secret is None:
        monkeypatch.delenv("CCA_CALLBACK_SECRET", raising=False)
    else:
        monkeypatch.setenv("CCA_CALLBACK_SECRET", secret)
    assert client.post(f"/workflows/{seeded_wf_id}/start", json={}).status_code == 202


def test_airflow_failure_is_502(client, seeded_wf_id, monkeypatch):
    monkeypatch.setenv("CCA_AIRFLOW_API_BASE_URL", "http://airflow.test")
    monkeypatch.setenv("CCA_AIRFLOW_API_USERNAME", "airflow")
    monkeypatch.setenv("CCA_AIRFLOW_API_PASSWORD", "airflow")
    service = ServicesObjectsFactory.get_airflow_start_dag_service()
    assert isinstance(service, AirflowStartDagServiceImpl)
    service._client = AirflowDagRunsClient(transport=httpx.MockTransport(_fail))
    response = client.post(f"/workflows/{seeded_wf_id}/start", json={})
    assert response.status_code == 502
    assert response.json()["detail"] == "engine start failed"
    listed = AppWfExecLogCtx(req=AppWfExecLogReq(workflow_id=seeded_wf_id))
    assert DaoObjectsFactory.get_app_wf_exec_log_dao().list(listed) == SUCCESS
    assert listed.resp.records


def test_path_is_in_openapi(client):
    spec = client.get("/openapi.json").json()
    assert "/workflows/{workflow_id}/start" in spec["paths"]
    assert "post" in spec["paths"]["/workflows/{workflow_id}/start"]
