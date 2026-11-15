"""Airflow DAG runs client: JWT then POST /api/v2/dags/{dag_id}/dagRuns."""

import json

import httpx
import pytest

from app.core.common.dtos.airflow_start_dag_dtos import (
    AirflowDagRunTriggerCtx,
    AirflowDagRunTriggerReq,
)
from app.core.common.return_codes import FAILURE, SUCCESS
from app.core.services.impl.airflow_dag_runs_client import AirflowDagRunsClient


def _handler(request: httpx.Request) -> httpx.Response:
    path = request.url.path
    if path == "/auth/token" and request.method == "POST":
        return httpx.Response(201, json={"access_token": "tok"})
    if path == "/api/v2/dags/download_cfpb_all/dagRuns" and request.method == "POST":
        body = json.loads(request.content.decode())
        assert body == {"logical_date": None, "conf": {"execution_id": "exec-1"}}
        assert request.headers.get("Authorization") == "Bearer tok"
        return httpx.Response(200, json={"dag_run_id": "manual__2026-11-14T00:00:00+00:00"})
    return httpx.Response(500, json={"detail": "unexpected"})


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("CCA_AIRFLOW_API_BASE_URL", "http://airflow.test")
    monkeypatch.setenv("CCA_AIRFLOW_API_USERNAME", "airflow")
    monkeypatch.setenv("CCA_AIRFLOW_API_PASSWORD", "airflow")
    return AirflowDagRunsClient(transport=httpx.MockTransport(_handler))


def test_trigger_returns_dag_run_id(client):
    ctx = AirflowDagRunTriggerCtx(
        req=AirflowDagRunTriggerReq(dag_id="download_cfpb_all", execution_id="exec-1")
    )
    assert client.trigger(ctx) == SUCCESS
    assert ctx.resp.dag_run_id == "manual__2026-11-14T00:00:00+00:00"


def test_token_failure_is_failure(monkeypatch):
    monkeypatch.setenv("CCA_AIRFLOW_API_BASE_URL", "http://airflow.test")
    monkeypatch.setenv("CCA_AIRFLOW_API_USERNAME", "airflow")
    monkeypatch.setenv("CCA_AIRFLOW_API_PASSWORD", "airflow")

    def bad_token(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"detail": "Unauthorized"})

    client = AirflowDagRunsClient(transport=httpx.MockTransport(bad_token))
    ctx = AirflowDagRunTriggerCtx(
        req=AirflowDagRunTriggerReq(dag_id="download_cfpb_all", execution_id="exec-1")
    )
    assert client.trigger(ctx) == FAILURE
