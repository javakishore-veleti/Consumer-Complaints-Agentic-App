"""Upsert-secrets service: list file + env + client outcomes (D42)."""

from pathlib import Path

import pytest

from app.core.common.dtos.airflow_upsert_secrets_dtos import (
    OUTCOME_CREATED,
    OUTCOME_MISSING,
    OUTCOME_UPDATED,
    AirflowUpsertSecretsCtx,
    UpsertSecretResult,
)
from app.core.common.return_codes import FAILURE, SUCCESS
from app.core.services.objects_factory import ServicesObjectsFactory


@pytest.fixture
def names_file(tmp_path: Path, monkeypatch):
    path = tmp_path / "Airflow_Variables_Upsert.txt"
    path.write_text("# comment\n\nCCA_CALLBACK_SECRET\nCCA_DB_URL\n", encoding="utf-8")
    monkeypatch.setenv("CCA_AIRFLOW_API_BASE_URL", "http://airflow.test")
    monkeypatch.setenv("CCA_AIRFLOW_API_USERNAME", "airflow")
    monkeypatch.setenv("CCA_AIRFLOW_API_PASSWORD", "airflow")
    # Point Settings at this file by patching get_settings path via monkeypatch on env is hard;
    # patch the path on the service by setting an env the impl reads — impl uses get_settings().
    from app.core.common import config

    real = config.get_settings

    def _settings():
        s = real()
        object.__setattr__(s, "airflow_variables_upsert_path", path)  # frozen — use replace pattern instead
        return s

    # Settings is frozen: rebuild via monkeypatch of get_settings
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


def test_missing_name_is_failure_and_others_still_run(names_file, monkeypatch):
    monkeypatch.setenv("CCA_CALLBACK_SECRET", "s3cret")
    monkeypatch.delenv("CCA_DB_URL", raising=False)

    from app.core.services.impl import airflow_upsert_secrets_service_impl as impl_mod
    from app.core.common.dtos.airflow_upsert_secrets_dtos import (
        AirflowVariablesUpsertCtx,
        UpsertSecretResult as R,
        OUTCOME_UPDATED,
    )
    from app.core.common.return_codes import SUCCESS as OK

    class FakeClient:
        def upsert_all(self, ctx: AirflowVariablesUpsertCtx) -> int:
            ctx.resp.results = [R(name=i.name, outcome=OUTCOME_UPDATED) for i in ctx.req.items]
            ctx.resp.code = OK
            return OK

    monkeypatch.setattr(impl_mod, "AirflowVariablesClient", lambda: FakeClient())
    ctx = AirflowUpsertSecretsCtx()
    code = ServicesObjectsFactory.get_airflow_upsert_secrets_service().upsert(ctx)
    assert code == FAILURE
    assert [(r.name, r.outcome) for r in ctx.resp.results] == [
        ("CCA_CALLBACK_SECRET", OUTCOME_UPDATED),
        ("CCA_DB_URL", OUTCOME_MISSING),
    ]


def test_all_present_is_success(names_file, monkeypatch):
    monkeypatch.setenv("CCA_CALLBACK_SECRET", "s3cret")
    monkeypatch.setenv("CCA_DB_URL", "sqlite:///x")

    from app.core.services.impl import airflow_upsert_secrets_service_impl as impl_mod
    from app.core.common.dtos.airflow_upsert_secrets_dtos import AirflowVariablesUpsertCtx, UpsertSecretResult as R
    from app.core.common.return_codes import SUCCESS as OK

    class FakeClient:
        def upsert_all(self, ctx: AirflowVariablesUpsertCtx) -> int:
            ctx.resp.results = [R(name=i.name, outcome=OUTCOME_CREATED) for i in ctx.req.items]
            ctx.resp.code = OK
            return OK

    monkeypatch.setattr(impl_mod, "AirflowVariablesClient", lambda: FakeClient())
    ctx = AirflowUpsertSecretsCtx()
    assert ServicesObjectsFactory.get_airflow_upsert_secrets_service().upsert(ctx) == SUCCESS
    assert all(r.outcome == OUTCOME_CREATED for r in ctx.resp.results)
