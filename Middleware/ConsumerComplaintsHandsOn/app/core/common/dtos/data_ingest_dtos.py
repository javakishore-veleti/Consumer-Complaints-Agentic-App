"""Ctx, Req and Resp for the data_ingest_log table (see DESIGN.md, section 2.1).

These are plain objects with no database code. The DAO (dao/impl) converts them
to and from SQLAlchemy table classes.
"""

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class DataIngestRecord:
    """One data_ingest_log row, as returned to callers."""

    id: str
    purpose: str
    status: str
    run_id: str | None = None
    message: str | None = None
    requested_at: datetime | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None


@dataclass
class DataIngestReq:
    """What the caller asks the DAO to do. A field left as None means "not given"."""

    id: str | None = None
    purpose: str | None = None
    status: str | None = None
    run_id: str | None = None
    message: str | None = None
    limit: int | None = None  # list only
    offset: int | None = None  # list only


@dataclass
class DataIngestResp:
    """What the DAO hands back: the rows that were created, read or updated."""

    records: list[DataIngestRecord] = field(default_factory=list)


@dataclass
class DataIngestCtx:
    """The only argument a data-ingest DAO method takes."""

    req: DataIngestReq = field(default_factory=DataIngestReq)
    resp: DataIngestResp = field(default_factory=DataIngestResp)
