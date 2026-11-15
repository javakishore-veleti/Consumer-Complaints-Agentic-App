"""Ctx, Req and Resp for starting a registered workflow (DESIGN.md D68)."""

from dataclasses import dataclass, field


@dataclass
class StartWfReq:
    workflow_id: str | None = None
    mio_id: str | None = None
    dataset_location_id: str | None = None


@dataclass
class StartWfResp:
    execution_id: str | None = None
    engine_type: str | None = None
    code: int = 0


@dataclass
class StartWfCtx:
    req: StartWfReq = field(default_factory=StartWfReq)
    resp: StartWfResp = field(default_factory=StartWfResp)
