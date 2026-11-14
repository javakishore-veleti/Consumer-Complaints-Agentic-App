"""Ctx, Req and Resp of the dataset status service (it updates the log and system_datasets together)."""

from dataclasses import dataclass, field

from app.core.common.dtos.data_ingest_dtos import DataIngestRecord
from app.core.common.dtos.system_datasets_dtos import SystemDatasetRecord
from app.core.common.dtos.transaction_dtos import TransactionalCtx


@dataclass
class DatasetStatusReq:
    usecase: str | None = None
    status: str | None = None  # a data_ingest_log status: started, completed or failed (record only)
    run_id: str | None = None
    message: str | None = None


@dataclass
class DatasetStatusResp:
    log: DataIngestRecord | None = None  # the log row that was created or changed
    dataset: SystemDatasetRecord | None = None  # the system_datasets row after the change
    records: list[SystemDatasetRecord] = field(default_factory=list)  # all rows (read)
    code: int = 0


@dataclass
class DatasetStatusCtx(TransactionalCtx):  # carries the transaction the service opens for the call
    operation: str = ""
    req: DatasetStatusReq = field(default_factory=DatasetStatusReq)
    resp: DatasetStatusResp = field(default_factory=DatasetStatusResp)
