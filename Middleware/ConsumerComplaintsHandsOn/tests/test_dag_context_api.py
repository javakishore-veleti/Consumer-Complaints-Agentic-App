"""GET /callbacks/workflow-executions/{id}/dag-context (M15 / #242)."""

import pytest

from app.core.common.dtos.app_wf_dtos import AppWfCtx, AppWfReq
from app.core.common.dtos.app_wf_exec_log_dtos import AppWfExecLogCtx, AppWfExecLogReq
from app.core.common.dtos.dataset_dtos import DatasetCtx, DatasetReq
from app.core.common.dtos.dataset_location_dtos import DatasetLocationCtx, DatasetLocationReq
from app.core.common.return_codes import SUCCESS
from app.core.dao.objects_factory import DaoObjectsFactory

SECRET = "s3cret-dag-context"
HEADERS = {"X-Callback-Secret": SECRET}


@pytest.fixture
def secret(monkeypatch):
    monkeypatch.setenv("CCA_CALLBACK_SECRET", SECRET)
    return SECRET


@pytest.fixture
def execution_with_dataset(data_dir):
    ds = DatasetCtx(req=DatasetReq(name="t_dag_ctx_ds", code="TDAGCTX"))
    assert DaoObjectsFactory.get_dataset_dao().create(ds) == SUCCESS
    dataset_id = ds.resp.records[0].id
    http = DatasetLocationCtx(
        req=DatasetLocationReq(
            dataset_id=dataset_id,
            location_type="http",
            path="https://example.test/data.zip",
        )
    )
    assert DaoObjectsFactory.get_dataset_location_dao().create(http) == SUCCESS
    local = DatasetLocationCtx(
        req=DatasetLocationReq(
            dataset_id=dataset_id,
            location_type="local",
            local_env_var_name="LOCAL_DATA_PATH_TDAGCTX",
        )
    )
    assert DaoObjectsFactory.get_dataset_location_dao().create(local) == SUCCESS

    wf = AppWfCtx(
        req=AppWfReq(
            workflow_name="t_dag_ctx_wf",
            engine_type="apache_airflow",
            engine_workflow_id="filter_cfpb_3_months",
            config={"dataset_code": "TDAGCTX", "months": 3},
        )
    )
    assert DaoObjectsFactory.get_app_wf_dao().create(wf) == SUCCESS
    ex = AppWfExecLogCtx(req=AppWfExecLogReq(workflow_id=wf.resp.records[0].id))
    assert DaoObjectsFactory.get_app_wf_exec_log_dao().create(ex) == SUCCESS
    return ex.resp.records[0].id


def test_dag_context_returns_config_and_locations(client, secret, execution_with_dataset):
    r = client.get(
        f"/callbacks/workflow-executions/{execution_with_dataset}/dag-context",
        headers=HEADERS,
    )
    assert r.status_code == 200
    body = r.json()
    assert body["execution_id"] == execution_with_dataset
    assert body["config_used"]["dataset_code"] == "TDAGCTX"
    assert body["config_used"]["months"] == 3
    assert body["dataset_locations"]["http"]["path"] == "https://example.test/data.zip"
    assert body["dataset_locations"]["local"]["local_env_var_name"] == "LOCAL_DATA_PATH_TDAGCTX"
    assert body["app_endpoint"] is None


def test_dag_context_requires_secret(client, secret, execution_with_dataset):
    r = client.get(f"/callbacks/workflow-executions/{execution_with_dataset}/dag-context")
    assert r.status_code == 401


def test_dag_context_unknown_execution_is_404(client, secret, data_dir):
    r = client.get(
        "/callbacks/workflow-executions/does-not-exist/dag-context",
        headers=HEADERS,
    )
    assert r.status_code == 404
