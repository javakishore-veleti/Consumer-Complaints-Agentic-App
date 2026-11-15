"""Airflow Variables HTTP client (D42): JWT then GET/POST/PATCH. Values never appear in assertions on logs."""

import httpx
import pytest

from app.core.common.dtos.airflow_upsert_secrets_dtos import (
    OUTCOME_CREATED,
    OUTCOME_UPDATED,
    AirflowVariableUpsertItem,
    AirflowVariablesUpsertCtx,
    AirflowVariablesUpsertReq,
)
from app.core.common.return_codes import FAILURE, SUCCESS
from app.core.services.impl.airflow_variables_client import AirflowVariablesClient


def _handler(request: httpx.Request) -> httpx.Response:
    path = request.url.path
    if path == "/auth/token" and request.method == "POST":
        return httpx.Response(201, json={"access_token": "tok"})
    if path == "/api/v2/variables/NEW" and request.method == "GET":
        return httpx.Response(404, json={"detail": "Not Found"})
    if path == "/api/v2/variables" and request.method == "POST":
        return httpx.Response(201, json={"key": "NEW", "value": "x"})
    if path == "/api/v2/variables/OLD" and request.method == "GET":
        return httpx.Response(200, json={"key": "OLD", "value": "old"})
    if path == "/api/v2/variables/OLD" and request.method == "PATCH":
        return httpx.Response(200, json={"key": "OLD", "value": "new"})
    return httpx.Response(500, json={"detail": "unexpected"})


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("CCA_AIRFLOW_API_BASE_URL", "http://airflow.test")
    monkeypatch.setenv("CCA_AIRFLOW_API_USERNAME", "airflow")
    monkeypatch.setenv("CCA_AIRFLOW_API_PASSWORD", "airflow")
    transport = httpx.MockTransport(_handler)
    return AirflowVariablesClient(transport=transport)


def test_create_and_update(client):
    ctx = AirflowVariablesUpsertCtx(
        req=AirflowVariablesUpsertReq(
            items=[
                AirflowVariableUpsertItem(name="NEW", value="n"),
                AirflowVariableUpsertItem(name="OLD", value="new"),
            ]
        )
    )
    assert client.upsert_all(ctx) == SUCCESS
    assert [(r.name, r.outcome) for r in ctx.resp.results] == [
        ("NEW", OUTCOME_CREATED),
        ("OLD", OUTCOME_UPDATED),
    ]


def test_token_failure_is_failure(monkeypatch):
    monkeypatch.setenv("CCA_AIRFLOW_API_BASE_URL", "http://airflow.test")

    def bad_token(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"detail": "Unauthorized"})

    client = AirflowVariablesClient(transport=httpx.MockTransport(bad_token))
    ctx = AirflowVariablesUpsertCtx(
        req=AirflowVariablesUpsertReq(items=[AirflowVariableUpsertItem(name="A", value="v")])
    )
    assert client.upsert_all(ctx) == FAILURE
