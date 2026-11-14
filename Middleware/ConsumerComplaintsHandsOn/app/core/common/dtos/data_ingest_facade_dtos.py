"""Ctx, Req and Resp for the data ingest facade.

The facade ctx carries the DAO's own ctx (DataIngestCtx) as an additional member, which the facade tasks fill in
and hand to the DAO (DESIGN.md, section 2.1).
"""

from dataclasses import dataclass, field

from app.core.common.dtos.data_ingest_dtos import DataIngestCtx, DataIngestRecord
from app.core.common.return_codes import SUCCESS


@dataclass
class DataIngestFacadeReq:
    """What the API passes to the facade. A field left as None means "not given"."""

    id: str | None = None
    purpose: str | None = None
    status: str | None = None
    run_id: str | None = None
    message: str | None = None
    limit: int | None = None
    offset: int | None = None


@dataclass
class DataIngestFacadeResp:
    """What the facade hands back to the API."""

    records: list[DataIngestRecord] = field(default_factory=list)
    code: int = SUCCESS  # the result code of the call (also returned by the facade method)


@dataclass
class DataIngestFacadeCtx:
    operation: str = ""  # set by the facade (create, get, list, update, delete); tasks are singletons and read it here
    req: DataIngestFacadeReq = field(default_factory=DataIngestFacadeReq)
    resp: DataIngestFacadeResp = field(default_factory=DataIngestFacadeResp)
    data_ingest_ctx: DataIngestCtx = field(default_factory=DataIngestCtx)
