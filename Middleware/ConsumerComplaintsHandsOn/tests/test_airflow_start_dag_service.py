"""AirflowStartDagService: load execution, trigger DAG, store engine_run_id; status stays requested."""

import json

import httpx
import pytest

from app.core.common.dtos.airflow_start_dag_dtos import AirflowStartDagCtx, AirflowStartDagReq
from app.core.common.dtos.app_wf_dtos import AppWfCtx, AppWfReq
from app.core.common.dtos.app_wf_exec_log_dtos import AppWfExecLogCtx, AppWfExecLogReq
from app.core.common.return_codes import INVALID_INPUT, NOT_FOUND, SUCCESS
from app.core.common.singleton import SingletonMeta
from app.core.dao.objects_factory import DaoObjectsFactory
from app.core.services.impl.airflow_dag_runs_client import AirflowDagRunsClient
from app.core.services.impl.airflow_start_dag_service_impl import AirflowStartDagServiceImpl


def _handler(request: httpx.Request) -> httpx.Response:
    if request.url.path == "/auth/token":
        return httpx.Response(201, json={"access_token": "tok"})
    if request.method == "POST" and request.url.path.endswith("/dagRuns"):
        body = json.loads(request.content.decode())
        assert body["logical_date"] is None
        assert "execution_id" in body["conf"]
        return httpx.Response(200, json={"dag_run_id": "run-abc"})
    return httpx.Response(500)


@pytest.fixture(autouse=True)
def _reset_start_dag_singleton():
    SingletonMeta._instances.pop(AirflowStartDagServiceImpl, None)
    yield
    SingletonMeta._instances.pop(AirflowStartDagServiceImpl, None)


@pytest.fixture
def execution_id(data_dir, monkeypatch):
    monkeypatch.setenv("CCA_AIRFLOW_API_BASE_URL", "http://airflow.test")
    monkeypatch.setenv("CCA_AIRFLOW_API_USERNAME", "airflow")
    monkeypatch.setenv("CCA_AIRFLOW_API_PASSWORD", "airflow")
    wf = DaoObjectsFactory.get_app_wf_dao()
    wctx = AppWfCtx(
        req=AppWfReq(
            workflow_name="t_start_dag",
            engine_type="apache_airflow",
            engine_workflow_id="download_cfpb_all",
        )
    )
    assert wf.create(wctx) == SUCCESS
    elog = DaoObjectsFactory.get_app_wf_exec_log_dao()
    ectx = AppWfExecLogCtx(req=AppWfExecLogReq(workflow_id=wctx.resp.records[0].id))
    assert elog.create(ectx) == SUCCESS
    return ectx.resp.records[0].id


def test_start_stores_engine_run_id_and_keeps_requested(execution_id):
    service = AirflowStartDagServiceImpl(
        client=AirflowDagRunsClient(transport=httpx.MockTransport(_handler))
    )
    ctx = AirflowStartDagCtx(req=AirflowStartDagReq(execution_id=execution_id))
    assert service.start(ctx) == SUCCESS
    assert ctx.resp.engine_run_id == "run-abc"
    got = AppWfExecLogCtx(req=AppWfExecLogReq(id=execution_id))
    assert DaoObjectsFactory.get_app_wf_exec_log_dao().get(got) == SUCCESS
    row = got.resp.records[0]
    assert (row.engine_run_id, row.status) == ("run-abc", "requested")


def test_unknown_execution_is_not_found(data_dir):
    ctx = AirflowStartDagCtx(req=AirflowStartDagReq(execution_id="missing"))
    assert AirflowStartDagServiceImpl().start(ctx) == NOT_FOUND


def test_blank_execution_id_is_invalid():
    ctx = AirflowStartDagCtx(req=AirflowStartDagReq(execution_id="  "))
    assert AirflowStartDagServiceImpl().start(ctx) == INVALID_INPUT
