"""GET /workflows through HTTP (D66): portal list of registered workflows."""

import pytest

from app.core.common.dtos.app_wf_dtos import AppWfCtx, AppWfReq
from app.core.common.return_codes import SUCCESS
from app.core.dao.objects_factory import DaoObjectsFactory

URL = "/workflows"
SEEDED = ["download_cfpb_all", "filter_cfpb_3_months", "ingest_cfpb_all"]


def test_seeded_registry_lists_download_cfpb_all(client):
    response = client.get(URL)
    assert response.status_code == 200
    body = response.json()
    assert [row["workflow_name"] for row in body] == SEEDED
    for row in body:
        assert "config" not in row


def test_lists_workflows_without_config(client):
    for name in ("t_z", "t_y"):
        ctx = AppWfCtx(
            req=AppWfReq(
                workflow_name=name,
                engine_type="apache_airflow",
                engine_workflow_id="dag",
                config={"x": 1},
            )
        )
        assert DaoObjectsFactory.get_app_wf_dao().create(ctx) == SUCCESS

    body = client.get(URL).json()
    assert [row["workflow_name"] for row in body] == [*SEEDED, "t_y", "t_z"]
    for row in body:
        assert set(row) == {"id", "workflow_name", "engine_type", "engine_workflow_id", "enabled"}
        assert "config" not in row


@pytest.mark.parametrize("secret", [None, "any-value"])
def test_no_callback_secret_is_required(client, monkeypatch, secret):
    if secret is None:
        monkeypatch.delenv("CCA_CALLBACK_SECRET", raising=False)
    else:
        monkeypatch.setenv("CCA_CALLBACK_SECRET", secret)
    assert client.get(URL).status_code == 200


def test_path_is_in_openapi(client):
    spec = client.get("/openapi.json").json()
    assert "/workflows" in spec["paths"]
    assert "get" in spec["paths"]["/workflows"]
