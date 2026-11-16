"""StartWfService prepares ingest+exec; facade triggers via WorkflowEngine (D68/D73)."""

import json

import httpx
import pytest

from app.core.common.dtos.app_wf_dtos import AppWfCtx, AppWfReq
from app.core.common.dtos.app_wf_exec_log_dtos import AppWfExecLogCtx, AppWfExecLogReq
from app.core.common.dtos.mio_acl_dtos import MioAclCtx, MioAclReq
from app.core.common.dtos.mio_dtos import MioCtx, MioReq
from app.core.common.dtos.mio_ingest_log_dtos import MioIngestLogCtx, MioIngestLogReq
from app.core.common.dtos.mio_workflow_dtos import MioWorkflowCtx, MioWorkflowReq
from app.core.common.dtos.start_wf_dtos import StartWfCtx, StartWfReq
from app.core.common.dtos.start_wf_facade_dtos import StartWfFacadeCtx
from app.core.common.return_codes import INVALID_INPUT, SUCCESS
from app.core.dao.objects_factory import DaoObjectsFactory
from app.core.facades.objects_factory import FacadesObjectsFactory
from app.core.services.impl.airflow_dag_runs_client import AirflowDagRunsClient
from app.core.services.impl.airflow_start_dag_service_impl import AirflowStartDagServiceImpl
from app.core.services.objects_factory import ServicesObjectsFactory


def _handler(request: httpx.Request) -> httpx.Response:
    if request.url.path == "/auth/token":
        return httpx.Response(201, json={"access_token": "tok"})
    if request.method == "POST" and "/dagRuns" in request.url.path:
        body = json.loads(request.content.decode())
        assert body["logical_date"] is None
        assert body["conf"]["execution_id"]
        return httpx.Response(200, json={"dag_run_id": "run-start-1"})
    return httpx.Response(500)


@pytest.fixture(autouse=True)
def _airflow_env(monkeypatch):
    monkeypatch.setenv("CCA_AIRFLOW_API_BASE_URL", "http://airflow.test")
    monkeypatch.setenv("CCA_AIRFLOW_API_USERNAME", "airflow")
    monkeypatch.setenv("CCA_AIRFLOW_API_PASSWORD", "airflow")


def _workflow(name="t_start", enabled=True, engine_type="apache_airflow") -> str:
    ctx = AppWfCtx(
        req=AppWfReq(
            workflow_name=name,
            engine_type=engine_type,
            engine_workflow_id="download_cfpb_all",
            enabled=enabled,
        )
    )
    assert DaoObjectsFactory.get_app_wf_dao().create(ctx) == SUCCESS
    return ctx.resp.records[0].id


def _mio(name="t_mio_start", *, audience: str = "internal") -> str:
    ctx = MioCtx(req=MioReq(name=name, description="d"))
    assert DaoObjectsFactory.get_mio_dao().create(ctx) == SUCCESS
    mio_id = ctx.resp.records[0].id
    acl = MioAclCtx(req=MioAclReq(mio_id=mio_id, audience=audience))
    assert DaoObjectsFactory.get_mio_acl_dao().create(acl) == SUCCESS
    return mio_id


def _bind(mio_id: str, workflow_id: str) -> None:
    ctx = MioWorkflowCtx(req=MioWorkflowReq(mio_id=mio_id, workflow_id=workflow_id))
    assert DaoObjectsFactory.get_mio_workflow_dao().create(ctx) == SUCCESS


def test_creates_exec_without_mio(data_dir):
    wf_id = _workflow()
    ctx = StartWfCtx(req=StartWfReq(workflow_id=wf_id))
    assert ServicesObjectsFactory.get_start_wf_service().start(ctx) == SUCCESS
    assert ctx.resp.execution_id
    got = AppWfExecLogCtx(req=AppWfExecLogReq(id=ctx.resp.execution_id))
    assert DaoObjectsFactory.get_app_wf_exec_log_dao().get(got) == SUCCESS
    row = got.resp.records[0]
    assert row.workflow_id == wf_id and row.mios_ingest_log_id is None and row.status == "requested"


def test_creates_ingest_and_links_exec(data_dir):
    wf_id, mio_id = _workflow("t_start_mio"), _mio()
    _bind(mio_id, wf_id)
    ctx = StartWfCtx(req=StartWfReq(workflow_id=wf_id, mio_id=mio_id))
    assert ServicesObjectsFactory.get_start_wf_service().start(ctx) == SUCCESS
    got = AppWfExecLogCtx(req=AppWfExecLogReq(id=ctx.resp.execution_id))
    assert DaoObjectsFactory.get_app_wf_exec_log_dao().get(got) == SUCCESS
    ingest_id = got.resp.records[0].mios_ingest_log_id
    assert ingest_id
    ing = MioIngestLogCtx(req=MioIngestLogReq(id=ingest_id))
    assert DaoObjectsFactory.get_mio_ingest_log_dao().get(ing) == SUCCESS
    assert ing.resp.records[0].mio_id == mio_id and ing.resp.records[0].status == "requested"


def test_unbound_workflow_for_mio_is_invalid(data_dir):
    wf_ok, wf_other = _workflow("t_bound"), _workflow("t_unbound")
    mio_id = _mio("t_mio_bound")
    _bind(mio_id, wf_ok)
    ctx = StartWfCtx(req=StartWfReq(workflow_id=wf_other, mio_id=mio_id))
    assert ServicesObjectsFactory.get_start_wf_service().start(ctx) == INVALID_INPUT


def test_mio_with_no_allowed_workflows_is_invalid(data_dir):
    wf_id, mio_id = _workflow("t_empty_mio_wf"), _mio("t_mio_empty")
    ctx = StartWfCtx(req=StartWfReq(workflow_id=wf_id, mio_id=mio_id))
    assert ServicesObjectsFactory.get_start_wf_service().start(ctx) == INVALID_INPUT


def test_mio_start_denied_without_matching_audience(data_dir):
    wf_id, mio_id = _workflow("t_acl_deny"), _mio("t_mio_acl_deny", audience="internal")
    _bind(mio_id, wf_id)
    ctx = StartWfCtx(req=StartWfReq(workflow_id=wf_id, mio_id=mio_id, audience="partner"))
    assert ServicesObjectsFactory.get_start_wf_service().start(ctx) == INVALID_INPUT


def test_unknown_workflow_is_invalid(data_dir):
    ctx = StartWfCtx(req=StartWfReq(workflow_id="missing"))
    assert ServicesObjectsFactory.get_start_wf_service().start(ctx) == INVALID_INPUT


def test_disabled_workflow_is_invalid(data_dir):
    wf_id = _workflow("t_disabled", enabled=False)
    ctx = StartWfCtx(req=StartWfReq(workflow_id=wf_id))
    assert ServicesObjectsFactory.get_start_wf_service().start(ctx) == INVALID_INPUT


def test_non_airflow_engine_is_invalid(data_dir):
    wf_id = _workflow("t_step", engine_type="aws_step_functions")
    ctx = StartWfCtx(req=StartWfReq(workflow_id=wf_id))
    assert ServicesObjectsFactory.get_start_wf_service().start(ctx) == INVALID_INPUT


def test_blank_mio_id_is_invalid(data_dir):
    wf_id = _workflow("t_blank_mio")
    ctx = StartWfCtx(req=StartWfReq(workflow_id=wf_id, mio_id="  "))
    assert ServicesObjectsFactory.get_start_wf_service().start(ctx) == INVALID_INPUT


def test_unknown_mio_is_invalid(data_dir):
    wf_id = _workflow("t_bad_mio")
    ctx = StartWfCtx(req=StartWfReq(workflow_id=wf_id, mio_id="no-such-mio"))
    assert ServicesObjectsFactory.get_start_wf_service().start(ctx) == INVALID_INPUT


def test_unknown_dataset_location_is_invalid(data_dir):
    wf_id = _workflow("t_bad_loc")
    ctx = StartWfCtx(req=StartWfReq(workflow_id=wf_id, dataset_location_id="no-loc"))
    assert ServicesObjectsFactory.get_start_wf_service().start(ctx) == INVALID_INPUT


def test_facade_triggers_airflow_and_stores_run_id(data_dir):
    service = ServicesObjectsFactory.get_airflow_start_dag_service()
    assert isinstance(service, AirflowStartDagServiceImpl)
    service._client = AirflowDagRunsClient(transport=httpx.MockTransport(_handler))
    wf_id = _workflow("t_facade_af")
    ctx = StartWfFacadeCtx(req=StartWfReq(workflow_id=wf_id))
    assert FacadesObjectsFactory.get_start_wf_facade().start(ctx) == SUCCESS
    assert ctx.resp.execution_id
    got = AppWfExecLogCtx(req=AppWfExecLogReq(id=ctx.resp.execution_id))
    assert DaoObjectsFactory.get_app_wf_exec_log_dao().get(got) == SUCCESS
    assert got.resp.records[0].engine_run_id == "run-start-1"
