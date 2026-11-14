"""Ctx, Req and Resp for the mios_ingest_log table (each ingest of a MIO, DESIGN.md D50 and D58)."""

from dataclasses import dataclass, field
from datetime import datetime

from app.core.common.dtos.transaction_dtos import TransactionalCtx


@dataclass
class MioIngestLogRecord:
    id: str
    mio_id: str
    status: str
    message: str | None
    requested_at: datetime
    started_at: datetime | None
    finished_at: datetime | None
    rows_loaded: int | None
    batch_count: int | None
    increment_marker: str | None


@dataclass
class MioIngestLogReq:
    """A field left as None means "not given". id identifies one row. mio_id is what create needs and list filters
    on; status is a list filter; status, message, rows_loaded, batch_count and increment_marker are what update
    changes (create also takes the last four)."""

    id: str | None = None
    mio_id: str | None = None
    status: str | None = None
    message: str | None = None
    rows_loaded: int | None = None
    batch_count: int | None = None
    increment_marker: str | None = None
    limit: int | None = None
    offset: int | None = None


@dataclass
class MioIngestLogResp:
    records: list[MioIngestLogRecord] = field(default_factory=list)


@dataclass
class MioIngestLogCtx(TransactionalCtx):
    req: MioIngestLogReq = field(default_factory=MioIngestLogReq)
    resp: MioIngestLogResp = field(default_factory=MioIngestLogResp)
