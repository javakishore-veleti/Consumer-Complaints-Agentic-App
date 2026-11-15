"""HTTP client for Airflow 3 DAG runs API (JWT). Never logs tokens or passwords."""

from __future__ import annotations

import logging

import httpx

from app.core.common.config import get_settings
from app.core.common.dtos.airflow_start_dag_dtos import AirflowDagRunTriggerCtx
from app.core.common.return_codes import FAILURE, SUCCESS

logger = logging.getLogger(__name__)


class AirflowDagRunsClient:
    def __init__(self, transport: httpx.BaseTransport | None = None):
        self._transport = transport

    def trigger(self, ctx: AirflowDagRunTriggerCtx) -> int:
        ctx.resp.dag_run_id = None
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
                        "airflow dag run trigger failed: token status %s",
                        token_response.status_code,
                    )
                    ctx.resp.code = FAILURE
                    return FAILURE
                token = token_response.json().get("access_token")
                if not isinstance(token, str) or not token:
                    ctx.resp.code = FAILURE
                    return FAILURE
                headers = {"Authorization": f"Bearer {token}"}
                created = http.post(
                    f"/api/v2/dags/{ctx.req.dag_id}/dagRuns",
                    headers=headers,
                    json={
                        "logical_date": None,
                        "conf": {"execution_id": ctx.req.execution_id},
                    },
                )
                if created.status_code not in (200, 201):
                    logger.warning(
                        "airflow dag run trigger failed: create status %s",
                        created.status_code,
                    )
                    ctx.resp.code = FAILURE
                    return FAILURE
                dag_run_id = created.json().get("dag_run_id")
                if not isinstance(dag_run_id, str) or not dag_run_id:
                    ctx.resp.code = FAILURE
                    return FAILURE
                ctx.resp.dag_run_id = dag_run_id
        except httpx.HTTPError:
            logger.warning("airflow dag run trigger failed: unreachable")
            ctx.resp.code = FAILURE
            return FAILURE
        ctx.resp.code = SUCCESS
        return SUCCESS
