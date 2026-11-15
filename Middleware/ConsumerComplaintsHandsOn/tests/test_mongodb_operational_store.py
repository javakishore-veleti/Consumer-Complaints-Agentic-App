"""Mongo operational store (D79): factory, bootstrap, start+callback smoke via mongomock."""

from __future__ import annotations

import httpx
import mongomock
import pytest
from fastapi.testclient import TestClient

from app.api.objects_factory import ApiObjectsFactory
from app.core.common.dtos.app_wf_dtos import AppWfCtx
from app.core.common.dtos.app_wf_exec_log_dtos import AppWfExecLogCtx, AppWfExecLogReq
from app.core.common.dtos.mio_dtos import MioCtx, MioReq
from app.core.common.dtos.transaction_dtos import TransactionCtx
from app.core.common.return_codes import SUCCESS
from app.core.dao.impl.mongo.bootstrap import bootstrap_operational_mongo, drop_all_collections
from app.core.dao.impl.mongo.client import MongoDbOverride, reset_mongo_client, set_mongo_db_override
from app.core.dao.impl.mongo.mongo_app_wf_dao import MongoAppWfDao
from app.core.dao.impl.mongo.mongo_transaction_dao import MongoTransactionDao
from app.core.dao.objects_factory import DaoObjectsFactory
from app.core.services.impl.airflow_dag_runs_client import AirflowDagRunsClient
from app.core.services.impl.airflow_start_dag_service_impl import AirflowStartDagServiceImpl
from app.core.services.objects_factory import ServicesObjectsFactory


@pytest.fixture
def mongo_db(monkeypatch, tmp_path):
    monkeypatch.setenv("CCA_OPERATIONAL_STORE", "mongodb")
    monkeypatch.setenv("CCA_MONGO_OPERATIONAL_URL", "mongodb://localhost:27017/cca_operational_test")
    monkeypatch.setenv("CCA_DATA_DIR", str(tmp_path))
    monkeypatch.delenv("CCA_DB_URL", raising=False)
    db = mongomock.MongoClient().cca_operational_test
    set_mongo_db_override(MongoDbOverride(db=db))
    DaoObjectsFactory.reset()
    drop_all_collections()
    bootstrap_operational_mongo()
    yield db
    DaoObjectsFactory.reset()
    set_mongo_db_override(MongoDbOverride(db=None))
    reset_mongo_client()


def test_factory_registers_mongo_daos(mongo_db):
    DaoObjectsFactory.reset()
    DaoObjectsFactory.init()
    assert isinstance(DaoObjectsFactory.get_app_wf_dao(), MongoAppWfDao)
    assert isinstance(DaoObjectsFactory.get_transaction_dao(), MongoTransactionDao)


def test_seeded_workflows_and_mios(mongo_db):
    listed = AppWfCtx()
    assert DaoObjectsFactory.get_app_wf_dao().list(listed) == SUCCESS
    names = [r.workflow_name for r in listed.resp.records]
    assert "download_cfpb_all" in names
    assert "filter_cfpb_3_months" in names
    mio = MioCtx(req=MioReq(name="Customer complaints all 2026"))
    assert DaoObjectsFactory.get_mio_dao().get(mio) == SUCCESS


def test_transaction_rollback_restores_doc(mongo_db):
    listed = AppWfCtx()
    assert DaoObjectsFactory.get_app_wf_dao().list(listed) == SUCCESS
    wf_id = next(r.id for r in listed.resp.records if r.workflow_name == "download_cfpb_all")

    txn_dao = DaoObjectsFactory.get_transaction_dao()
    txn = TransactionCtx()
    assert txn_dao.begin(txn) == SUCCESS
    created = AppWfExecLogCtx(req=AppWfExecLogReq(workflow_id=wf_id), transaction=txn)
    assert DaoObjectsFactory.get_app_wf_exec_log_dao().create(created) == SUCCESS
    exec_id = created.resp.records[0].id
    assert mongo_db["app_workflows_exec_log"].find_one({"id": exec_id}) is not None
    assert txn_dao.rollback(txn) == SUCCESS
    assert mongo_db["app_workflows_exec_log"].find_one({"id": exec_id}) is None


def test_start_workflow_and_callback_persist_on_mongo(mongo_db, monkeypatch):
    secret = "mongo-via-env-callback-secret"
    monkeypatch.setenv("CCA_CALLBACK_SECRET", secret)
    monkeypatch.setenv("CCA_AIRFLOW_API_BASE_URL", "http://airflow.test")
    monkeypatch.setenv("CCA_AIRFLOW_API_USERNAME", "airflow")
    monkeypatch.setenv("CCA_AIRFLOW_API_PASSWORD", "airflow")

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/auth/token":
            return httpx.Response(201, json={"access_token": "tok"})
        if request.method == "POST" and "/dagRuns" in request.url.path:
            return httpx.Response(200, json={"dag_run_id": "mongo-run-1"})
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

    exec_doc = mongo_db["app_workflows_exec_log"].find_one({"id": execution_id})
    assert exec_doc is not None
    assert exec_doc["status"] == "requested"
    assert exec_doc["mios_ingest_log_id"]
    ingest_id = exec_doc["mios_ingest_log_id"]
    ingest_doc = mongo_db["mios_ingest_log"].find_one({"id": ingest_id})
    assert ingest_doc is not None
    assert ingest_doc["status"] == "requested"

    callback = client.post(
        f"/callbacks/workflow-executions/{execution_id}/status",
        json={"status": "started", "engine_run_id": "mongo-run-1"},
        headers={"X-Callback-Secret": secret},
    )
    assert callback.status_code == 200
    exec_doc = mongo_db["app_workflows_exec_log"].find_one({"id": execution_id})
    assert exec_doc["status"] == "started"
    assert exec_doc["engine_run_id"] == "mongo-run-1"
