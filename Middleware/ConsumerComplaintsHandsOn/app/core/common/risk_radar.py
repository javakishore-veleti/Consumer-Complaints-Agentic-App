"""Load Risk Radar golden fixture alerts (M53-0001 / #359)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import NamedTuple

from app.core.common.dtos.risk_radar_dtos import RiskRadarAlert

_REPO_ROOT = Path(__file__).resolve().parents[5]
_DEFAULT_FIXTURE = (
    _REPO_ROOT / "CICD" / "Local" / "iceberg" / "golden" / "risk_radar_golden_3m.json"
)


class LoadFixtureReq(NamedTuple):
    path: Path | None = None


def load_fixture_alerts(req: LoadFixtureReq) -> list[RiskRadarAlert]:
    path = req.path or _DEFAULT_FIXTURE
    data = json.loads(path.read_text(encoding="utf-8"))
    alerts: list[RiskRadarAlert] = []
    for raw in data.get("alerts") or []:
        alerts.append(
            RiskRadarAlert(
                id=str(raw.get("id") or ""),
                title=str(raw.get("title") or ""),
                severity=str(raw.get("severity") or ""),
                parent_org_id=str(raw.get("parent_org_id") or ""),
                primary_money_topic=str(raw.get("primary_money_topic") or ""),
                window_days=int(raw.get("window_days") or 0),
                current_count=int(raw.get("current_count") or 0),
                baseline_mean=float(raw.get("baseline_mean") or 0.0),
                z_score=float(raw.get("z_score") or 0.0),
                k_anon_ok=bool(raw.get("k_anon_ok")),
                drilldown_ast=dict(raw.get("drilldown_ast") or {}),
            )
        )
    return alerts
