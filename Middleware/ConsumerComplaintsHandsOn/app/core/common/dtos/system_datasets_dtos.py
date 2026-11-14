"""Ctx, Req and Resp for the system_datasets table (current state, one row per dataset and stage)."""

from dataclasses import dataclass, field
from datetime import datetime

from app.core.common.dtos.transaction_dtos import TransactionalCtx


@dataclass
class SystemDatasetRecord:
    dataset: str
    stage: str
    status: str
    last_log_id: str | None = None
    updated_at: datetime | None = None


@dataclass
class SystemDatasetsReq:
    """A field left as None means "not given". dataset + stage identify one row."""

    dataset: str | None = None
    stage: str | None = None
    status: str | None = None
    last_log_id: str | None = None


@dataclass
class SystemDatasetsResp:
    records: list[SystemDatasetRecord] = field(default_factory=list)


@dataclass
class SystemDatasetsCtx(TransactionalCtx):
    req: SystemDatasetsReq = field(default_factory=SystemDatasetsReq)
    resp: SystemDatasetsResp = field(default_factory=SystemDatasetsResp)
