"""Ctx, Req and Resp for the mios_datasets table (which datasets a MIO uses and where, DESIGN.md D49 and D57)."""

from dataclasses import dataclass, field
from datetime import datetime

from app.core.common.dtos.transaction_dtos import TransactionalCtx


@dataclass
class MioDatasetRecord:
    id: str
    mio_id: str
    dataset_id: str
    dataset_location_id: str
    created_at: datetime


@dataclass
class MioDatasetReq:
    """A field left as None means "not given". id identifies one row (get, update, delete)."""

    id: str | None = None
    mio_id: str | None = None
    dataset_id: str | None = None
    dataset_location_id: str | None = None


@dataclass
class MioDatasetResp:
    records: list[MioDatasetRecord] = field(default_factory=list)


@dataclass
class MioDatasetCtx(TransactionalCtx):
    req: MioDatasetReq = field(default_factory=MioDatasetReq)
    resp: MioDatasetResp = field(default_factory=MioDatasetResp)
