"""Service ctx for listing/reading app_endpoints (D85 / #156)."""

from dataclasses import dataclass, field
from datetime import datetime

from app.core.common.return_codes import SUCCESS


@dataclass
class AppEndpointEntry:
    id: str
    name: str
    category: str
    from_dataset_location_id: str | None
    from_env_var_name: str | None
    to_dataset_location_id: str | None
    to_env_var_name: str | None
    credentials_ref: str | None
    description: str | None
    enabled: bool
    created_at: datetime
    updated_at: datetime


@dataclass
class AppEndpointListReq:
    id: str | None = None
    category: str | None = None
    enabled: bool | None = None
    name: str | None = None


@dataclass
class AppEndpointListResp:
    entries: list[AppEndpointEntry] = field(default_factory=list)
    code: int = SUCCESS


@dataclass
class AppEndpointListCtx:
    req: AppEndpointListReq = field(default_factory=AppEndpointListReq)
    resp: AppEndpointListResp = field(default_factory=AppEndpointListResp)
