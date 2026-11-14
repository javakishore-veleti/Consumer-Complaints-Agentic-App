"""Interface of the DAO for the app_workflows table (one DAO per table)."""

from abc import abstractmethod

from app.core.common.dtos.app_wf_dtos import AppWfCtx
from app.core.common.singleton import SingletonMeta


class AppWfDao(metaclass=SingletonMeta):
    """A singleton (every implementation is). Every method takes one AppWfCtx and returns an integer code
    (app.core.common.return_codes). Results are written to ctx.resp.records. If ctx.transaction is set, the call
    joins that transaction and the transaction's owner commits."""

    @abstractmethod
    def create(self, ctx: AppWfCtx) -> int:
        """Needs req.workflow_name (up to 100 characters), req.engine_type (an EngineType value) and
        req.engine_workflow_id (up to 255 characters). Optional: config (default NULL), enabled (default true).
        INVALID_INPUT for a missing or unacceptable field, CONFLICT if the name is taken."""

    @abstractmethod
    def get(self, ctx: AppWfCtx) -> int:
        """Needs req.id or req.workflow_name (the id wins). INVALID_INPUT if neither is given, NOT_FOUND if there is
        no such row."""

    @abstractmethod
    def list(self, ctx: AppWfCtx) -> int:
        """Optional filters: req.engine_type, req.enabled. Ordered by workflow_name."""

    @abstractmethod
    def update(self, ctx: AppWfCtx) -> int:
        """Needs req.id. Changes the given workflow_name, engine_type, engine_workflow_id, config and enabled and
        sets updated_at. NOT_FOUND if there is no such row, INVALID_INPUT for an unacceptable field, CONFLICT if the
        new name belongs to another row."""

    @abstractmethod
    def delete(self, ctx: AppWfCtx) -> int:
        """Needs req.id. The deleted row is returned. NOT_FOUND if there is no such row."""
