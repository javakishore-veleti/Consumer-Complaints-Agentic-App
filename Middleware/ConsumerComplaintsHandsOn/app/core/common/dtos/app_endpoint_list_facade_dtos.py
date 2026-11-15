"""Facade ctx for app_endpoints list/read (#156)."""

from dataclasses import dataclass, field

from app.core.common.dtos.app_endpoint_list_dtos import AppEndpointListCtx, AppEndpointListReq, AppEndpointListResp


@dataclass
class AppEndpointListFacadeCtx:
    req: AppEndpointListReq = field(default_factory=AppEndpointListReq)
    resp: AppEndpointListResp = field(default_factory=AppEndpointListResp)
    service_ctx: AppEndpointListCtx = field(default_factory=AppEndpointListCtx)
