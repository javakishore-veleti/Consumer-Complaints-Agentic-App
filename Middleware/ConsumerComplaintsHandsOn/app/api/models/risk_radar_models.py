from typing import Any

from pydantic import BaseModel, Field


class RiskRadarQuery(BaseModel):
    source: str = "fixture"


class RiskRadarBody(BaseModel):
    source: str = "fixture"


class RiskRadarAlertOut(BaseModel):
    id: str
    title: str
    severity: str
    parent_org_id: str = ""
    primary_money_topic: str = ""
    window_days: int = 0
    current_count: int = 0
    baseline_mean: float = 0.0
    z_score: float = 0.0
    k_anon_ok: bool = False
    drilldown_ast: dict[str, Any] = Field(default_factory=dict)


class RiskRadarOut(BaseModel):
    alerts: list[RiskRadarAlertOut]
    source: str = "fixture"
    error: str = Field(default="")
