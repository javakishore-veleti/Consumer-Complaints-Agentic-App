"""The only module of the services package that may import from services/impl.

Static methods return the singleton, typed as the interface.
"""

from app.core.services.dataset_status_service import DatasetStatusService
from app.core.services.wf_exec_status_service import WfExecStatusService


class ServicesObjectsFactory:
    @staticmethod
    def get_dataset_status_service() -> DatasetStatusService:
        from app.core.services.impl.dataset_status_service_impl import DatasetStatusServiceImpl

        return DatasetStatusServiceImpl()

    @staticmethod
    def get_wf_exec_status_service() -> WfExecStatusService:
        from app.core.services.impl.wf_exec_status_service_impl import WfExecStatusServiceImpl

        return WfExecStatusServiceImpl()
