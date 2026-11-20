"""The status callback through HTTP (D60): the secret (D59), the error mapping, and duplicate and out-of-order calls."""

import pytest

from app.core.common.dtos.app_wf_dtos import AppWfCtx, AppWfReq
from app.core.common.dtos.app_wf_exec_log_dtos import AppWfExecLogCtx, AppWfExecLogReq
from app.core.common.dtos.mio_dtos import MioCtx, MioReq
from app.core.common.dtos.mio_ingest_log_dtos import MioIngestLogCtx, MioIngestLogReq
from app.core.common.return_codes import SUCCESS
from app.core.dao.objects_factory import DaoObjectsFactory

SECRET = "s3cret-value-for-tests"
HEADERS = {"X-Callback-Secret": SECRET}
SEEDED_MIO = "Customer complaints 3 months 2026"


def _url(execution_id):
    return f"/callbacks/workflow-executions/{execution_id}/status"


def _execution_status(execution_id):
    ctx = AppWfExecLogCtx(req=AppWfExecLogReq(id=execution_id))
    assert DaoObjectsFactory.get_app_wf_exec_log_dao().get(ctx) == SUCCESS
    return ctx.resp.records[0].status


@pytest.fixture
def secret(monkeypatch):
    monkeypatch.setenv("CCA_CALLBACK_SECRET", SECRET)
    return SECRET


@pytest.fixture
def ingest_id(data_dir):
    mio = MioCtx(req=MioReq(name=SEEDED_MIO))
    assert DaoObjectsFactory.get_mio_dao().get(mio) == SUCCESS
    ctx = MioIngestLogCtx(req=MioIngestLogReq(mio_id=mio.resp.records[0].id))
    assert DaoObjectsFactory.get_mio_ingest_log_dao().create(ctx) == SUCCESS
    return ctx.resp.records[0].id


@pytest.fixture
def new_execution(data_dir):
    """Creates an execution of a fresh workflow; pass an ingest id to attach it to that ingest."""
    workflow = AppWfCtx(req=AppWfReq(workflow_name="t_callback", engine_type="apache_airflow", engine_workflow_id="d"))
    assert DaoObjectsFactory.get_app_wf_dao().create(workflow) == SUCCESS

    def create(ingest=None):
        ctx = AppWfExecLogCtx(req=AppWfExecLogReq(workflow_id=workflow.resp.records[0].id, mios_ingest_log_id=ingest))
        assert DaoObjectsFactory.get_app_wf_exec_log_dao().create(ctx) == SUCCESS
        return ctx.resp.records[0].id

    return create


def test_started_then_completed_moves_the_execution_and_its_ingest(client, secret, new_execution, ingest_id):
    execution_id = new_execution(ingest_id)
    started = client.post(_url(execution_id), json={"status": "started", "engine_run_id": "run-1"}, headers=HEADERS)
    assert started.status_code == 200
    body = started.json()
    assert (body["execution"]["id"], body["execution"]["status"]) == (execution_id, "started")
    assert body["execution"]["engine_run_id"] == "run-1"
    assert body["execution"]["mios_ingest_log_id"] == ingest_id
    assert (body["ingest"]["id"], body["ingest"]["status"]) == (ingest_id, "started")

    done = client.post(
        _url(execution_id),
        json={"status": "completed", "message": "ok", "rows_loaded": 1500, "batch_count": 3, "increment_marker": "m"},
        headers=HEADERS,
    )
    assert done.status_code == 200
    ingest = done.json()["ingest"]
    assert (ingest["status"], ingest["message"], ingest["rows_loaded"]) == ("completed", "ok", 1500)
    assert (ingest["batch_count"], ingest["increment_marker"]) == (3, "m")
    assert ingest["finished_at"] is not None


def test_an_execution_without_an_ingest_returns_a_null_ingest(client, secret, new_execution):
    response = client.post(_url(new_execution()), json={"status": "started"}, headers=HEADERS)
    assert response.status_code == 200
    assert response.json()["ingest"] is None
    assert response.json()["execution"]["status"] == "started"


def test_status_without_invoked_json_does_not_append_engine_chronicle(client, secret, new_execution):
    execution_id = new_execution()
    response = client.post(_url(execution_id), json={"status": "started"}, headers=HEADERS)
    assert response.status_code == 200
    chronicle = response.json()["execution"]["wf_engine_data_json"]
    assert chronicle is None or chronicle.get("invocations") == []


def test_status_with_invoked_info_appends_engine_chronicle(client, secret, new_execution):
    execution_id = new_execution()
    response = client.post(
        _url(execution_id),
        json={
            "status": "started",
            "engine_run_id": "run-x",
            "invoked_info": {"dag_id": "filter_cfpb_3_months", "task": "sense"},
        },
        headers=HEADERS,
    )
    assert response.status_code == 200
    invocations = response.json()["execution"]["wf_engine_data_json"]["invocations"]
    assert len(invocations) == 1
    assert invocations[0]["invoked_for"] == "started"
    assert invocations[0]["invoked_info"]["dag_id"] == "filter_cfpb_3_months"
    assert "invoked_configs" not in invocations[0]


def test_a_duplicate_call_is_200_with_the_same_body(client, secret, new_execution, ingest_id):
    execution_id = new_execution(ingest_id)
    first = client.post(_url(execution_id), json={"status": "started"}, headers=HEADERS)
    again = client.post(_url(execution_id), json={"status": "started"}, headers=HEADERS)
    assert (first.status_code, again.status_code) == (200, 200)
    assert again.json() == first.json()


def test_an_out_of_order_call_is_409_and_changes_nothing(client, secret, new_execution, ingest_id):
    execution_id = new_execution(ingest_id)
    response = client.post(_url(execution_id), json={"status": "completed"}, headers=HEADERS)
    assert response.status_code == 409
    assert response.json() == {"detail": "status change not allowed in the current state"}
    assert _execution_status(execution_id) == "requested"


def test_a_late_call_after_a_final_status_is_409(client, secret, new_execution):
    execution_id = new_execution()
    assert client.post(_url(execution_id), json={"status": "failed"}, headers=HEADERS).status_code == 200
    assert client.post(_url(execution_id), json={"status": "started"}, headers=HEADERS).status_code == 409
    assert client.post(_url(execution_id), json={"status": "failed"}, headers=HEADERS).status_code == 200


def test_an_unknown_execution_is_404(client, secret):
    response = client.post(_url("no-such-execution"), json={"status": "started"}, headers=HEADERS)
    assert response.status_code == 404
    assert response.json() == {"detail": "workflow execution not found"}


@pytest.mark.parametrize(
    "body",
    [
        {"status": "requested"},
        {"status": "bogus"},
        {},
        {"status": "started", "rows_loaded": -1},
        {"status": "started", "rows_loaded": "5"},
        {"status": "started", "batch_count": True},
        {"status": "started", "engine_run_id": "r" * 129},
        {"status": "started", "increment_marker": "m" * 256},
        {"status": "started", "unknown_field": 1},
    ],
)
def test_an_invalid_body_is_422_and_changes_nothing(client, secret, new_execution, body):
    execution_id = new_execution()
    assert client.post(_url(execution_id), json=body, headers=HEADERS).status_code == 422
    assert _execution_status(execution_id) == "requested"


def test_a_volume_beyond_the_column_maximum_is_422_from_the_service(client, secret, new_execution, ingest_id):
    execution_id = new_execution(ingest_id)
    response = client.post(_url(execution_id), json={"status": "started", "batch_count": 2**31}, headers=HEADERS)
    assert response.status_code == 422
    assert response.json() == {"detail": "invalid request"}
    assert _execution_status(execution_id) == "requested"


@pytest.mark.parametrize("headers", [{}, {"X-Callback-Secret": "wrong"}])
def test_without_the_right_secret_it_is_401_and_nothing_changes(client, secret, new_execution, headers):
    execution_id = new_execution()
    response = client.post(_url(execution_id), json={"status": "started"}, headers=headers)
    assert response.status_code == 401
    assert response.json() == {"detail": "missing or wrong callback secret"}
    assert _execution_status(execution_id) == "requested"


def test_without_a_configured_secret_it_is_401(client, monkeypatch, new_execution):
    monkeypatch.delenv("CCA_CALLBACK_SECRET", raising=False)
    response = client.post(_url(new_execution()), json={"status": "started"}, headers={"X-Callback-Secret": ""})
    assert response.status_code == 401


def test_a_malformed_json_body_is_422_before_the_secret_check(client, secret, new_execution):
    """Accepted (D59, D60): FastAPI parses the body before the router's dependency runs."""
    execution_id = new_execution()
    response = client.post(_url(execution_id), content=b"{not json", headers={"Content-Type": "application/json"})
    assert response.status_code == 422
    assert _execution_status(execution_id) == "requested"


def test_openapi_lists_the_callback(client):
    paths = client.get("/openapi.json").json()["paths"]
    assert set(paths["/callbacks/workflow-executions/{execution_id}/status"]) == {"post"}
