"""Ctx, Req and Resp for the datasets_location table (where a dataset lives, DESIGN.md D49 and D57)."""

from dataclasses import dataclass, field
from datetime import datetime

from app.core.common.dtos.transaction_dtos import TransactionalCtx


@dataclass
class DatasetLocationRecord:
    id: str
    dataset_id: str
    location_type: str
    path: str | None
    local_env_var_name: str | None
    credentials_ref: str | None
    description: str | None
    created_at: datetime
    updated_at: datetime


@dataclass
class DatasetLocationReq:
    """A field left as None means "not given". id identifies one row (get, update, delete)."""

    id: str | None = None
    dataset_id: str | None = None
    location_type: str | None = None
    path: str | None = None
    local_env_var_name: str | None = None
    credentials_ref: str | None = None
    description: str | None = None


@dataclass
class DatasetLocationResp:
    records: list[DatasetLocationRecord] = field(default_factory=list)


@dataclass
class DatasetLocationCtx(TransactionalCtx):
    req: DatasetLocationReq = field(default_factory=DatasetLocationReq)
    resp: DatasetLocationResp = field(default_factory=DatasetLocationResp)
