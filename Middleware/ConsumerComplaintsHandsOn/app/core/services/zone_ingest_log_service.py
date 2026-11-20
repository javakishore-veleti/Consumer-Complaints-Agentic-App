"""Service interface for zone ingest_log_* (M55-0011 / #391)."""

from abc import abstractmethod

from app.core.common.dtos.zone_ingest_log_dtos import ZoneIngestLogCtx
from app.core.common.singleton import SingletonMeta


class ZoneIngestLogService(metaclass=SingletonMeta):
    @abstractmethod
    def create(self, ctx: ZoneIngestLogCtx) -> int: ...

    @abstractmethod
    def get(self, ctx: ZoneIngestLogCtx) -> int: ...

    @abstractmethod
    def list(self, ctx: ZoneIngestLogCtx) -> int: ...

    @abstractmethod
    def update(self, ctx: ZoneIngestLogCtx) -> int: ...

    @abstractmethod
    def delete(self, ctx: ZoneIngestLogCtx) -> int: ...

    @abstractmethod
    def claim_pending(self, ctx: ZoneIngestLogCtx) -> int: ...

    @abstractmethod
    def complete(self, ctx: ZoneIngestLogCtx) -> int: ...

    @abstractmethod
    def reset_failed(self, ctx: ZoneIngestLogCtx) -> int: ...
