"""Ctx for upserting selected .env names into Airflow Variables (DESIGN.md D42)."""

from dataclasses import dataclass, field

from app.core.common.return_codes import SUCCESS

OUTCOME_CREATED = "created"
OUTCOME_UPDATED = "updated"
OUTCOME_MISSING = "missing"
OUTCOME_SKIPPED = "skipped"  # optional name unset (M10-0012 / #219)


@dataclass
class UpsertSecretResult:
    name: str
    outcome: str  # created | updated | missing | skipped


@dataclass
class AirflowUpsertSecretsReq:
    pass  # no body; reserved for future filters


@dataclass
class AirflowUpsertSecretsResp:
    results: list[UpsertSecretResult] = field(default_factory=list)
    code: int = SUCCESS


@dataclass
class AirflowUpsertSecretsCtx:
    req: AirflowUpsertSecretsReq = field(default_factory=AirflowUpsertSecretsReq)
    resp: AirflowUpsertSecretsResp = field(default_factory=AirflowUpsertSecretsResp)


@dataclass
class AirflowVariableUpsertItem:
    name: str
    value: str


@dataclass
class AirflowVariablesUpsertReq:
    items: list[AirflowVariableUpsertItem] = field(default_factory=list)


@dataclass
class AirflowVariablesUpsertResp:
    results: list[UpsertSecretResult] = field(default_factory=list)
    code: int = SUCCESS


@dataclass
class AirflowVariablesUpsertCtx:
    req: AirflowVariablesUpsertReq = field(default_factory=AirflowVariablesUpsertReq)
    resp: AirflowVariablesUpsertResp = field(default_factory=AirflowVariablesUpsertResp)
