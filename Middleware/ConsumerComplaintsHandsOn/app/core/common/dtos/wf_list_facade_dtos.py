"""Ctx of the workflow list facade. Reuses the service's Req and Resp; carries list_ctx."""

from dataclasses import dataclass, field

from app.core.common.dtos.wf_list_dtos import WfListCtx, WfListReq, WfListResp


@dataclass
class WfListFacadeCtx:
    req: WfListReq = field(default_factory=WfListReq)
    resp: WfListResp = field(default_factory=WfListResp)
    list_ctx: WfListCtx = field(default_factory=WfListCtx)
