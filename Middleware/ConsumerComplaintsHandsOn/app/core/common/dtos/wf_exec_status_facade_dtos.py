"""Ctx of the workflow execution status facade. The request and the response have the same shape as the service's,
so they reuse its Req and Resp; the facade ctx carries the service's own ctx as an additional member (section 2.1)."""

from dataclasses import dataclass, field

from app.core.common.dtos.wf_exec_status_dtos import WfExecStatusCtx, WfExecStatusReq, WfExecStatusResp


@dataclass
class WfExecStatusFacadeCtx:
    req: WfExecStatusReq = field(default_factory=WfExecStatusReq)
    resp: WfExecStatusResp = field(default_factory=WfExecStatusResp)
    status_ctx: WfExecStatusCtx = field(default_factory=WfExecStatusCtx)
