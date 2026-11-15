"""Interface of the DAO for the mios_workflows table (one DAO per table)."""

from abc import abstractmethod

from app.core.common.dtos.mio_workflow_dtos import MioWorkflowCtx
from app.core.common.singleton import SingletonMeta


class MioWorkflowDao(metaclass=SingletonMeta):
    """A singleton. Every method takes one MioWorkflowCtx and returns an integer code.
    Results go to ctx.resp.records. Binding is catalog data (D84); never derived from a MIO name (D57)."""

    @abstractmethod
    def create(self, ctx: MioWorkflowCtx) -> int:
        """Needs req.mio_id and req.workflow_id. NOT_FOUND if either parent is missing;
        CONFLICT if the MIO already allows that workflow."""

    @abstractmethod
    def get(self, ctx: MioWorkflowCtx) -> int:
        """Needs req.id."""

    @abstractmethod
    def list(self, ctx: MioWorkflowCtx) -> int:
        """Optional filters: req.mio_id, req.workflow_id. Ordered by created_at, id."""

    @abstractmethod
    def delete(self, ctx: MioWorkflowCtx) -> int:
        """Needs req.id. The deleted row is returned."""
