"""The callback secret through HTTP (D59): a router protected the way #43 and later stories attach it, and the
existing endpoints that stay open. The protected router exists only in this test; the app gains no endpoint."""

import pytest
from fastapi import APIRouter, Depends, FastAPI
from fastapi.testclient import TestClient

from app.api.objects_factory import ApiObjectsFactory

SECRET = "s3cret-value-for-tests"
CALLS = []


def _ping() -> dict[str, str]:
    CALLS.append("ping")
    return {"status": "ok"}


@pytest.fixture
def protected():
    """A throwaway app with one router protected at include time, exactly as ApiObjectsFactory will do it."""
    CALLS.clear()
    router = APIRouter(prefix="/test-callbacks")
    router.add_api_route("/ping", _ping, methods=["POST"])
    app = FastAPI()
    app.include_router(router, dependencies=[Depends(ApiObjectsFactory.get_callback_secret_auth())])
    return TestClient(app)


@pytest.fixture
def secret(monkeypatch):
    monkeypatch.setenv("CCA_CALLBACK_SECRET", SECRET)
    return SECRET


def test_the_right_secret_reaches_the_endpoint(protected, secret):
    response = protected.post("/test-callbacks/ping", headers={"X-Callback-Secret": secret})
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert CALLS == ["ping"]


@pytest.mark.parametrize("headers", [{}, {"X-Callback-Secret": "wrong"}, {"X-Callback-Secret": ""}])
def test_a_missing_or_wrong_secret_is_401_and_the_endpoint_never_runs(protected, secret, headers):
    response = protected.post("/test-callbacks/ping", headers=headers)
    assert response.status_code == 401
    assert response.json() == {"detail": "missing or wrong callback secret"}
    assert response.headers["WWW-Authenticate"] == "X-Callback-Secret"
    assert secret not in response.text
    assert CALLS == []


def test_the_secret_in_another_header_is_refused(protected, secret):
    response = protected.post("/test-callbacks/ping", headers={"Authorization": f"Bearer {secret}"})
    assert response.status_code == 401


def test_without_a_configured_secret_the_router_is_closed(protected, monkeypatch):
    monkeypatch.delenv("CCA_CALLBACK_SECRET", raising=False)
    assert protected.post("/test-callbacks/ping", headers={"X-Callback-Secret": ""}).status_code == 401
    assert protected.post("/test-callbacks/ping", headers={"X-Callback-Secret": "anything"}).status_code == 401
    monkeypatch.setenv("CCA_CALLBACK_SECRET", "   ")
    assert protected.post("/test-callbacks/ping", headers={"X-Callback-Secret": ""}).status_code == 401
    assert CALLS == []


@pytest.mark.parametrize("configured", [SECRET, None])
def test_health_and_the_existing_endpoints_stay_open(client, monkeypatch, configured):
    if configured is None:
        monkeypatch.delenv("CCA_CALLBACK_SECRET", raising=False)
    else:
        monkeypatch.setenv("CCA_CALLBACK_SECRET", configured)
    assert client.get("/health").status_code == 200
    assert client.get("/data-ingest-logs").status_code == 200
