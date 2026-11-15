"""Start a workflow run in its engine (DESIGN.md D73). One implementation per engine type."""

from abc import abstractmethod

from app.core.common.dtos.workflow_engine_dtos import WorkflowEngineCtx
from app.core.common.singleton import SingletonMeta


class WorkflowEngine(metaclass=SingletonMeta):
    @property
    @abstractmethod
    def engine_type(self) -> str:
        """Short engine code (EngineType value), e.g. apache_airflow."""

    @abstractmethod
    def start(self, ctx: WorkflowEngineCtx) -> int:
        """Start a run for ctx.req.execution_id; return SUCCESS or an error code."""
