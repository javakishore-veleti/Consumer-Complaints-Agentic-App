"""HTTP tests for POST /management/airflow/upsert-secrets (D42, D59)."""

from pathlib import Path

import pytest

from app.core.common import config
from app.core.common.dtos.airflow_upsert_secrets_dtos import (
    OUTCOME_CREATED,
    OUTCOME_UPDATED,
    AirflowVariablesUpsertCtx,
    UpsertSecretResult,
)
from app.core.common.return_codes import FAILURE, SUCCESS

SECRET = "upsert-callback-secret-for-tests"
SECRET_VALUE = "never-leak-this-callback-secret"
DB_URL_VALUE = "sqlite:///never-leak-this-db-url"
URL = "/management/airflow/upsert-secrets"


@pytest.fixture
def names_file(tmp_path: Path, monkeypatch):
    path = tmp_path / "Airflow_Variables_Upsert.txt"
    path.write_text("# comment\n\nCCA_CALLBACK_SECRET\nCCA_DB_URL\n", encoding="utf-8")
    monkeypatch.setenv("CCA_AIRFLOW_API_BASE_URL", "http://airflow.test")
    monkeypatch.setenv("CCA_AIRFLOW_API_USERNAME", "airflow")
    monkeypatch.setenv("CCA_AIRFLOW_API_PASSWORD", "airflow")

    real = config.get_settings

    def fake_get_settings():
        base = real()
        return config.Settings(
            db_url=base.db_url,
            data_dir=base.data_dir,
            callback_secret=base.callback_secret,
            airflow_api_base_url=base.airflow_api_base_url,
            airflow_api_username=base.airflow_api_username,
            airflow_api_password=base.airflow_api_password,
            airflow_variables_upsert_path=path,
        )

    monkeypatch.setattr(config, "get_settings", fake_get_settings)
    from app.core.services.impl import airflow_upsert_secrets_service_impl as impl_mod

    monkeypatch.setattr(impl_mod, "get_settings", fake_get_settings)
    return path


@pytest.fixture
def secret(monkeypatch):
    monkeypatch.setenv("CCA_CALLBACK_SECRET", SECRET)
    return SECRET


def _fake_client(outcome: str = OUTCOME_UPDATED, code: int = SUCCESS):
    class FakeClient:
        def upsert_all(self, ctx: AirflowVariablesUpsertCtx) -> int:
            if code != SUCCESS:
                ctx.resp.code = FAILURE
                ctx.resp.results = []
                return FAILURE
            ctx.resp.results = [UpsertSecretResult(name=i.name, outcome=outcome) for i in ctx.req.items]
            ctx.resp.code = SUCCESS
            return SUCCESS

    return FakeClient


def test_right_secret_returns_200_without_values(client, secret, names_file, monkeypatch):
    monkeypatch.setenv("CCA_CALLBACK_SECRET", SECRET_VALUE)
    monkeypatch.setenv("CCA_DB_URL", DB_URL_VALUE)
    from app.core.services.impl import airflow_upsert_secrets_service_impl as impl_mod

    monkeypatch.setattr(impl_mod, "AirflowVariablesClient", _fake_client(OUTCOME_CREATED))

    response = client.post(URL, headers={"X-Callback-Secret": SECRET_VALUE})
    assert response.status_code == 200
    body = response.json()
    assert body == {
        "results": [
            {"name": "CCA_CALLBACK_SECRET", "outcome": "created"},
            {"name": "CCA_DB_URL", "outcome": "created"},
        ]
    }
    assert SECRET_VALUE not in response.text
    assert DB_URL_VALUE not in response.text
    assert all("value" not in r for r in body["results"])


def test_missing_env_name_is_422_with_missing_outcome(client, secret, names_file, monkeypatch):
    monkeypatch.setenv("CCA_CALLBACK_SECRET", SECRET_VALUE)
    monkeypatch.delenv("CCA_DB_URL", raising=False)
    from app.core.services.impl import airflow_upsert_secrets_service_impl as impl_mod

    monkeypatch.setattr(impl_mod, "AirflowVariablesClient", _fake_client(OUTCOME_UPDATED))

    response = client.post(URL, headers={"X-Callback-Secret": SECRET_VALUE})
    assert response.status_code == 422
    body = response.json()
    assert body == {
        "results": [
            {"name": "CCA_CALLBACK_SECRET", "outcome": "updated"},
            {"name": "CCA_DB_URL", "outcome": "missing"},
        ]
    }
    assert SECRET_VALUE not in response.text
    assert "value" not in {k for r in body["results"] for k in r}


@pytest.mark.parametrize("headers", [{}, {"X-Callback-Secret": "wrong"}, {"X-Callback-Secret": ""}])
def test_wrong_or_missing_secret_is_401(client, secret, names_file, headers):
    response = client.post(URL, headers=headers)
    assert response.status_code == 401
    assert response.json() == {"detail": "missing or wrong callback secret"}
    assert SECRET not in response.text


def test_client_failure_without_missing_is_502(client, secret, names_file, monkeypatch):
    monkeypatch.setenv("CCA_CALLBACK_SECRET", SECRET_VALUE)
    monkeypatch.setenv("CCA_DB_URL", DB_URL_VALUE)
    from app.core.services.impl import airflow_upsert_secrets_service_impl as impl_mod

    monkeypatch.setattr(impl_mod, "AirflowVariablesClient", _fake_client(code=FAILURE))

    response = client.post(URL, headers={"X-Callback-Secret": SECRET_VALUE})
    assert response.status_code == 502
    assert response.json() == {"detail": "airflow variables upsert failed"}
    assert SECRET_VALUE not in response.text
    assert DB_URL_VALUE not in response.text
