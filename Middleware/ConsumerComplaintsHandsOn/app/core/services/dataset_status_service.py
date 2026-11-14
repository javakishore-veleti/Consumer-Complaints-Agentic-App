"""Interface of the service that keeps data_ingest_log and system_datasets in step (DESIGN.md, section 2.4)."""

from abc import abstractmethod

from app.core.common.dtos.dataset_status_dtos import DatasetStatusCtx
from app.core.common.singleton import SingletonMeta


class DatasetStatusService(metaclass=SingletonMeta):
    """A singleton (every implementation is). Every method takes one DatasetStatusCtx and returns an integer code
    (app.core.common.return_codes), also written to ctx.resp.code. request() and record() change the log and
    the dataset row in ONE transaction: either both change or neither does."""

    @abstractmethod
    def request(self, ctx: DatasetStatusCtx) -> int:
        """A run of req.usecase is asked for: writes a log row (status requested) and sets the dataset row to
        running. CONFLICT if that dataset and stage is already running. INVALID_INPUT for an unknown usecase.
        The new log row is in resp.log, the dataset row in resp.dataset."""

    @abstractmethod
    def record(self, ctx: DatasetStatusCtx) -> int:
        """A run reports its outcome (the Airflow callback): req.usecase, req.status (started, completed or
        failed), optional run_id and message. Changes the newest log row of the usecase (status rules of D30) and
        the dataset row together. NOT_FOUND if the usecase was never requested; CONFLICT for a change that is
        not allowed, or when run_id belongs to an older run. The same report twice is accepted."""

    @abstractmethod
    def read(self, ctx: DatasetStatusCtx) -> int:
        """All system_datasets rows, in resp.records (what the portal's accordions show)."""
