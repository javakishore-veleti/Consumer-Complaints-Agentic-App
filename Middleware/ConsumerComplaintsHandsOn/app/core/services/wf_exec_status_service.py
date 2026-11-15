"""Interface of the service that records a status an engine reports for one workflow execution (DESIGN.md D60)."""

from abc import abstractmethod

from app.core.common.dtos.wf_exec_status_dtos import WfExecStatusCtx
from app.core.common.singleton import SingletonMeta


class WfExecStatusService(metaclass=SingletonMeta):
    """A singleton (every implementation is). Every method takes one WfExecStatusCtx and returns an integer code
    (app.core.common.return_codes), also written to ctx.resp.code."""

    @abstractmethod
    def record(self, ctx: WfExecStatusCtx) -> int:
        """Needs req.execution_id and req.status (started, completed or failed). Changes the execution (D30 rules,
        with engine_run_id and message) and, when it has a mios_ingest_log_id, its ingest row, in ONE transaction:
        either both change or neither does.

        The ingest row follows the execution: started moves a requested ingest to started; failed moves an ingest
        that is not final to failed; completed moves a started ingest to completed once every execution of that
        ingest is completed. Any other move is skipped, so the ingest never makes the call fail: a final ingest
        stays as it is. The callback's message goes to the ingest only when its status moves; rows_loaded,
        batch_count and increment_marker are written to the ingest on every call that gives them.

        INVALID_INPUT for a blank execution_id, any other status, or an invalid field; NOT_FOUND for an unknown
        execution; CONFLICT for a move of the execution D30 does not allow (nothing changes); the same status again
        is SUCCESS. NOT_FOUND and CONFLICT always describe the execution: when the ingest side fails any other way
        the call is FAILURE and nothing changes. resp.execution and resp.ingest hold the rows after the call."""
