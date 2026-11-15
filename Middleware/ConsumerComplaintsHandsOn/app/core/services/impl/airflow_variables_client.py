"""HTTP client for Airflow 3 Variables API (JWT). Never logs values or tokens. Helpers are inlined (D37)."""

from __future__ import annotations

import logging

import httpx

from app.core.common.config import get_settings
from app.core.common.dtos.airflow_upsert_secrets_dtos import (
    OUTCOME_CREATED,
    OUTCOME_UPDATED,
    AirflowVariablesUpsertCtx,
    UpsertSecretResult,
)
from app.core.common.return_codes import FAILURE, SUCCESS

logger = logging.getLogger(__name__)


class AirflowVariablesClient:
    def __init__(self, transport: httpx.BaseTransport | None = None):
        self._transport = transport

    def upsert_all(self, ctx: AirflowVariablesUpsertCtx) -> int:
        ctx.resp.results = []
        settings = get_settings()
        if not settings.airflow_api_username or settings.airflow_api_password is None:
            ctx.resp.code = FAILURE
            return FAILURE
        timeout = httpx.Timeout(5.0, read=30.0)
        try:
            with httpx.Client(
                base_url=settings.airflow_api_base_url,
                timeout=timeout,
                transport=self._transport,
            ) as http:
                token_response = http.post(
                    "/auth/token",
                    json={
                        "username": settings.airflow_api_username,
                        "password": settings.airflow_api_password,
                    },
                )
                if token_response.status_code not in (200, 201):
                    logger.warning(
                        "airflow variables upsert failed: token status %s", token_response.status_code
                    )
                    ctx.resp.code = FAILURE
                    return FAILURE
                token = token_response.json().get("access_token")
                if not isinstance(token, str) or not token:
                    ctx.resp.code = FAILURE
                    return FAILURE
                headers = {"Authorization": f"Bearer {token}"}
                for item in ctx.req.items:
                    get = http.get(f"/api/v2/variables/{item.name}", headers=headers)
                    if get.status_code == 404:
                        created = http.post(
                            "/api/v2/variables",
                            headers=headers,
                            json={"key": item.name, "value": item.value},
                        )
                        if created.status_code not in (200, 201):
                            logger.warning(
                                "airflow variables upsert failed: create status %s", created.status_code
                            )
                            ctx.resp.code = FAILURE
                            return FAILURE
                        ctx.resp.results.append(
                            UpsertSecretResult(name=item.name, outcome=OUTCOME_CREATED)
                        )
                        continue
                    if get.status_code != 200:
                        logger.warning("airflow variables upsert failed: get status %s", get.status_code)
                        ctx.resp.code = FAILURE
                        return FAILURE
                    patched = http.patch(
                        f"/api/v2/variables/{item.name}",
                        headers=headers,
                        json={"key": item.name, "value": item.value},
                    )
                    if patched.status_code != 200:
                        logger.warning(
                            "airflow variables upsert failed: patch status %s", patched.status_code
                        )
                        ctx.resp.code = FAILURE
                        return FAILURE
                    ctx.resp.results.append(UpsertSecretResult(name=item.name, outcome=OUTCOME_UPDATED))
        except httpx.HTTPError:
            logger.warning("airflow variables upsert failed: unreachable")
            ctx.resp.code = FAILURE
            return FAILURE
        ctx.resp.code = SUCCESS
        return SUCCESS
