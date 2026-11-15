"""Ctx of the MIO status facade. Reuses the service's Req and Resp; carries the service ctx as status_ctx."""

from dataclasses import dataclass, field

from app.core.common.dtos.mio_status_dtos import MioStatusCtx, MioStatusReq, MioStatusResp


@dataclass
class MioStatusFacadeCtx:
    req: MioStatusReq = field(default_factory=MioStatusReq)
    resp: MioStatusResp = field(default_factory=MioStatusResp)
    status_ctx: MioStatusCtx = field(default_factory=MioStatusCtx)
