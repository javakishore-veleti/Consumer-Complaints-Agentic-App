"""Facade ctx for starting a registered workflow (DESIGN.md D68)."""

from dataclasses import dataclass, field

from app.core.common.dtos.start_wf_dtos import StartWfCtx, StartWfReq, StartWfResp


@dataclass
class StartWfFacadeCtx:
    req: StartWfReq = field(default_factory=StartWfReq)
    resp: StartWfResp = field(default_factory=StartWfResp)
    start_ctx: StartWfCtx | None = None
