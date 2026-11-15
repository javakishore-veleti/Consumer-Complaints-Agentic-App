"""WorkflowEngine interface, Airflow impl, and factory lookup (D73 / #83)."""

import json

import httpx
import pytest

from app.core.common.app_types_constants import EngineType
from app.core.common.dtos.app_wf_dtos import AppWfCtx, AppWfReq
from app.core.common.dtos.app_wf_exec_log_dtos import AppWfExecLogCtx, AppWfExecLogReq
from app.core.common.dtos.workflow_engine_dtos import WorkflowEngineCtx, WorkflowEngineReq
from app.core.common.return_codes import INVALID_INPUT, SUCCESS
from app.core.dao.objects_factory import DaoObjectsFactory
from app.core.services.impl.airflow_dag_runs_client import AirflowDagRunsClient
from app.core.services.impl.airflow_start_dag_service_impl import AirflowStartDagServiceImpl
from app.core.services.impl.apache_airflow_workflow_engine_impl import (
    ApacheAirflowWorkflowEngineImpl,
)
from app.core.services.objects_factory import ServicesObjectsFactory
from app.core.services.workflow_engine import WorkflowEngine


def _handler(request: httpx.Request) -> httpx.Response:
    if request.url.path == "/auth/token":
        return httpx.Response(201, json={"access_token": "tok"})
    if request.method == "POST" and "/dagRuns" in request.url.path:
        body = json.loads(request.content.decode())
        assert body["logical_date"] is None
        assert body["conf"]["execution_id"]
        return httpx.Response(200, json={"dag_run_id": "run-engine-1"})
    return httpx.Response(500)


@pytest.fixture(autouse=True)
def _airflow_env(monkeypatch):
    monkeypatch.setenv("CCA_AIRFLOW_API_BASE_URL", "http://airflow.test")
    monkeypatch.setenv("CCA_AIRFLOW_API_USERNAME", "airflow")
    monkeypatch.setenv("CCA_AIRFLOW_API_PASSWORD", "airflow")


def _execution_id(data_dir) -> str:
    wf = AppWfCtx(
        req=AppWfReq(
            workflow_name="t_engine_af",
            engine_type="apache_airflow",
            engine_workflow_id="download_cfpb_all",
        )
    )
    assert DaoObjectsFactory.get_app_wf_dao().create(wf) == SUCCESS
    elog = AppWfExecLogCtx(req=AppWfExecLogReq(workflow_id=wf.resp.records[0].id))
    assert DaoObjectsFactory.get_app_wf_exec_log_dao().create(elog) == SUCCESS
    return elog.resp.records[0].id


def test_factory_returns_engines_in_fixed_order():
    engines = ServicesObjectsFactory.get_workflow_engines()
    assert engines
    assert all(isinstance(e, WorkflowEngine) for e in engines)
    assert engines[0].engine_type == EngineType.APACHE_AIRFLOW.value
    assert ServicesObjectsFactory.get_workflow_engines() == engines
    assert engines[0] is ApacheAirflowWorkflowEngineImpl()


def test_airflow_engine_start_stores_run_id(data_dir):
    service = ServicesObjectsFactory.get_airflow_start_dag_service()
    assert isinstance(service, AirflowStartDagServiceImpl)
    service._client = AirflowDagRunsClient(transport=httpx.MockTransport(_handler))
    engines = ServicesObjectsFactory.get_workflow_engines()
    engine = next(e for e in engines if e.engine_type == EngineType.APACHE_AIRFLOW.value)
    execution_id = _execution_id(data_dir)
    ctx = WorkflowEngineCtx(req=WorkflowEngineReq(execution_id=execution_id))
    assert engine.start(ctx) == SUCCESS
    assert ctx.resp.engine_run_id == "run-engine-1"
    got = AppWfExecLogCtx(req=AppWfExecLogReq(id=execution_id))
    assert DaoObjectsFactory.get_app_wf_exec_log_dao().get(got) == SUCCESS
    assert got.resp.records[0].engine_run_id == "run-engine-1"


def test_unknown_engine_type_is_invalid_input():
    from app.core.common.dtos.start_wf_dtos import StartWfResp
    from app.core.common.dtos.start_wf_facade_dtos import StartWfFacadeCtx
    from app.core.facades.impl.start_wf.tasks.start_wf_trigger_engine_task import (
        StartWfTriggerEngineTask,
    )

    engines = ServicesObjectsFactory.get_workflow_engines()
    assert next((e for e in engines if e.engine_type == "aws_step_functions"), None) is None
    ctx = StartWfFacadeCtx(resp=StartWfResp(execution_id="exec-x", engine_type="aws_step_functions"))
    assert StartWfTriggerEngineTask().execute(ctx) == INVALID_INPUT
    assert ctx.resp.code == INVALID_INPUT


def test_trigger_task_source_has_no_airflow_imports():
    from pathlib import Path

    path = (
        Path(__file__).resolve().parents[1]
        / "app/core/facades/impl/start_wf/tasks/start_wf_trigger_engine_task.py"
    )
    text = path.read_text()
    assert "airflow" not in text.lower()
    assert "AirflowStartDag" not in text
