"""Ctx, Req and Resp for the datasets table (the catalog of datasets, DESIGN.md D49 and D57)."""

from dataclasses import dataclass, field
from datetime import datetime

from app.core.common.dtos.transaction_dtos import TransactionalCtx


@dataclass
class DatasetRecord:
    id: str
    name: str
    code: str
    description: str | None
    created_at: datetime
    updated_at: datetime


@dataclass
class DatasetReq:
    """A field left as None means "not given". id (or, for get, name) identifies one row."""

    id: str | None = None
    name: str | None = None
    code: str | None = None
    description: str | None = None


@dataclass
class DatasetResp:
    records: list[DatasetRecord] = field(default_factory=list)


@dataclass
class DatasetCtx(TransactionalCtx):
    req: DatasetReq = field(default_factory=DatasetReq)
    resp: DatasetResp = field(default_factory=DatasetResp)
