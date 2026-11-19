"""Ctx for Intellect Risk Radar (M53-0001 / #359)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class RiskRadarAlert:
    id: str = ""
    title: str = ""
    severity: str = ""
    parent_org_id: str = ""
    primary_money_topic: str = ""
    window_days: int = 0
    current_count: int = 0
    baseline_mean: float = 0.0
    z_score: float = 0.0
    k_anon_ok: bool = False
    drilldown_ast: dict[str, Any] = field(default_factory=dict)


@dataclass
class RiskRadarReq:
    source: str = "fixture"


@dataclass
class RiskRadarResp:
    alerts: list[RiskRadarAlert] = field(default_factory=list)
    source: str = "fixture"
    code: int = 0
    error: str = ""


@dataclass
class RiskRadarCtx:
    req: RiskRadarReq = field(default_factory=RiskRadarReq)
    resp: RiskRadarResp = field(default_factory=RiskRadarResp)
