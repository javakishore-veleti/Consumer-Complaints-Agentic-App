"""Risk Radar alerts: fixture or warehouse (M53-0001 / #359)."""

from __future__ import annotations

import os
import subprocess
from typing import NamedTuple

from app.core.common.dtos.risk_radar_dtos import RiskRadarCtx
from app.core.common.return_codes import FAILURE, INVALID_INPUT, SUCCESS
from app.core.common.risk_radar import LoadFixtureReq, load_fixture_alerts
from app.core.services.risk_radar_service import RiskRadarService


class _ContainerRunningReq(NamedTuple):
    container: str


def _container_running(req: _ContainerRunningReq) -> bool:
    try:
        out = subprocess.check_output(
            ["docker", "inspect", "-f", "{{.State.Running}}", req.container],
            text=True,
            stderr=subprocess.DEVNULL,
        )
        return out.strip() == "true"
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


class RiskRadarServiceImpl(RiskRadarService):
    def run(self, ctx: RiskRadarCtx) -> int:
        ctx.resp.alerts = []
        ctx.resp.error = ""
        source = (ctx.req.source or "fixture").strip().lower()
        if source not in {"fixture", "warehouse"}:
            ctx.resp.code = INVALID_INPUT
            ctx.resp.error = "source must be fixture or warehouse"
            ctx.resp.source = source
            return INVALID_INPUT
        ctx.resp.source = source
        if source == "fixture":
            ctx.resp.alerts = load_fixture_alerts(LoadFixtureReq())
            ctx.resp.code = SUCCESS
            return SUCCESS
        container = os.environ.get("CCA_ICEBERG_SPARK_CONTAINER", "cca-iceberg-spark")
        if not _container_running(_ContainerRunningReq(container)):
            ctx.resp.code = FAILURE
            ctx.resp.error = "warehouse unavailable"
            return FAILURE
        # Warehouse path reuses fixture cohort shapes until live velocity DAG lands.
        ctx.resp.alerts = load_fixture_alerts(LoadFixtureReq())
        ctx.resp.code = SUCCESS
        return SUCCESS
