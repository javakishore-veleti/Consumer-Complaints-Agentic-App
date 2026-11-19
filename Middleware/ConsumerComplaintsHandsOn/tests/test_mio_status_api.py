"""GET /mios/status through HTTP (D61): the portal's read of every MIO with its latest ingest and executions."""

import pytest

from app.core.common.dtos.app_wf_dtos import AppWfCtx, AppWfReq
from app.core.common.dtos.app_wf_exec_log_dtos import AppWfExecLogCtx, AppWfExecLogReq
from app.core.common.dtos.mio_dtos import MioCtx, MioReq
from app.core.common.dtos.mio_ingest_log_dtos import MioIngestLogCtx, MioIngestLogReq
from app.core.common.return_codes import SUCCESS
from app.core.dao.objects_factory import DaoObjectsFactory

SEEDED_NAMES = [
    "Customer complaints 12 months 2026",
    "Customer complaints 3 months 2026",
    "Customer complaints 6 months 2026",
    "Customer complaints 9 months 2026",
    "Customer complaints all 2026",
]
SEEDED_3M = "Customer complaints 3 months 2026"
URL = "/mios/status"


@pytest.fixture
def seeded_3m_id(data_dir):
    mio = MioCtx(req=MioReq(name=SEEDED_3M))
    assert DaoObjectsFactory.get_mio_dao().get(mio) == SUCCESS
    return mio.resp.records[0].id


def test_lists_every_seeded_mio_with_null_ingest(client):
    response = client.get(URL)
    assert response.status_code == 200
    body = response.json()
    assert [row["name"] for row in body] == SEEDED_NAMES
    assert all(row["latest_ingest"] is None for row in body)
    by_name = {row["name"]: row for row in body}
    assert [w["workflow_name"] for w in by_name["Customer complaints all 2026"]["allowed_workflows"]] == [
        "download_cfpb_all",
        "index_cfpb_all",
        "index_cfpb_chroma",
        "index_cfpb_pgvector",
        "index_cfpb_redis",
        "ingest_cfpb_all",
        "ingest_cfpb_imports_wrapper",
    ]
    assert [w["workflow_name"] for w in by_name["Customer complaints 3 months 2026"]["allowed_workflows"]] == [
        "filter_cfpb_3_months",
        "hydrate_chroma_signatures_3m",
        "hydrate_curated_iceberg_3m",
        "hydrate_raw_iceberg_3m",
        "hydrate_refined_iceberg_3m",
        "hydrate_taxonomy_mode2_3m",
        "index_cfpb_chroma",
        "index_cfpb_pgvector",
        "index_cfpb_redis",
        "ingest_cfpb_imports_wrapper",
    ]
    assert by_name["Customer complaints 6 months 2026"]["allowed_workflows"] == []


def test_nests_latest_ingest_and_executions(client, seeded_3m_id):
    older = MioIngestLogCtx(req=MioIngestLogReq(mio_id=seeded_3m_id, message="old"))
    assert DaoObjectsFactory.get_mio_ingest_log_dao().create(older) == SUCCESS
    newer = MioIngestLogCtx(req=MioIngestLogReq(mio_id=seeded_3m_id, message="new", rows_loaded=10))
    assert DaoObjectsFactory.get_mio_ingest_log_dao().create(newer) == SUCCESS
    newer_id = newer.resp.records[0].id
    workflow = AppWfCtx(req=AppWfReq(workflow_name="t_api_status", engine_type="apache_airflow", engine_workflow_id="d"))
    assert DaoObjectsFactory.get_app_wf_dao().create(workflow) == SUCCESS
    execution = AppWfExecLogCtx(
        req=AppWfExecLogReq(workflow_id=workflow.resp.records[0].id, mios_ingest_log_id=newer_id)
    )
    assert DaoObjectsFactory.get_app_wf_exec_log_dao().create(execution) == SUCCESS

    body = client.get(URL).json()
    entry = next(row for row in body if row["id"] == seeded_3m_id)
    ingest = entry["latest_ingest"]
    assert (ingest["id"], ingest["message"], ingest["rows_loaded"]) == (newer_id, "new", 10)
    assert len(ingest["executions"]) == 1
    assert ingest["executions"][0]["id"] == execution.resp.records[0].id
    assert "config_used" not in ingest["executions"][0]


def test_mio_id_filter_returns_one(client, seeded_3m_id):
    response = client.get(URL, params={"mio_id": seeded_3m_id})
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["id"] == seeded_3m_id


def test_unknown_mio_id_is_404(client):
    response = client.get(URL, params={"mio_id": "no-such-mio"})
    assert response.status_code == 404
    assert response.json() == {"detail": "mio not found"}


def test_blank_mio_id_is_422(client):
    response = client.get(URL, params={"mio_id": "   "})
    assert response.status_code == 422
    assert response.json() == {"detail": "invalid request"}


@pytest.mark.parametrize("secret", [None, "any-value"])
def test_no_callback_secret_is_required(client, monkeypatch, secret):
    if secret is None:
        monkeypatch.delenv("CCA_CALLBACK_SECRET", raising=False)
    else:
        monkeypatch.setenv("CCA_CALLBACK_SECRET", secret)
    assert client.get(URL).status_code == 200


def test_path_is_in_openapi(client):
    spec = client.get("/openapi.json").json()
    assert "/mios/status" in spec["paths"]
    assert "get" in spec["paths"]["/mios/status"]
