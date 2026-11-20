"""HTTP tests for GET /workflow-logs (M55-0012 / #394)."""

from app.core.common.dtos.app_wf_dtos import AppWfCtx, AppWfReq
from app.core.common.dtos.app_wf_exec_log_dtos import AppWfExecLogCtx, AppWfExecLogReq
from app.core.common.return_codes import SUCCESS
from app.core.dao.objects_factory import DaoObjectsFactory


def _workflow_id_by_name(name: str) -> str:
    ctx = AppWfCtx(req=AppWfReq(workflow_name=name))
    assert DaoObjectsFactory.get_app_wf_dao().get(ctx) == SUCCESS
    return ctx.resp.records[0].id


def _seed_exec(name: str):
    ex = AppWfExecLogCtx(req=AppWfExecLogReq(workflow_id=_workflow_id_by_name(name)))
    assert DaoObjectsFactory.get_app_wf_exec_log_dao().create(ex) == SUCCESS
    return ex.resp.records[0]


def test_workflow_logs_category_import_and_db_ingest(client):
    _seed_exec("download_cfpb_all")
    _seed_exec("ingest_cfpb_all")
    _seed_exec("ingest_cfpb_imports_wrapper")
    _seed_exec("hydrate_raw_iceberg_3m")

    imports = client.get("/workflow-logs", params={"category": "import", "limit": 30})
    assert imports.status_code == 200, imports.text
    names = {r["workflow_name"] for r in imports.json()}
    assert "download_cfpb_all" in names
    assert "ingest_cfpb_imports_wrapper" in names
    assert "ingest_cfpb_all" not in names
    assert "hydrate_raw_iceberg_3m" not in names
    assert all(r["display_status"] == "started" for r in imports.json())

    db = client.get("/workflow-logs", params={"category": "db_ingest"})
    assert db.status_code == 200
    db_names = {r["workflow_name"] for r in db.json()}
    assert "ingest_cfpb_all" in db_names
    assert "ingest_cfpb_imports_wrapper" not in db_names


def test_workflow_logs_limit_max_30_and_openapi(client):
    listed = client.get("/workflow-logs", params={"limit": 30})
    assert listed.status_code == 200
    bad = client.get("/workflow-logs", params={"limit": 31})
    assert bad.status_code == 422
    paths = client.get("/openapi.json").json()["paths"]
    assert "/workflow-logs" in paths
