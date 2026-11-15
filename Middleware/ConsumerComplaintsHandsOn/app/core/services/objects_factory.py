"""The only module of the services package that may import from services/impl.

Static methods return the singleton, typed as the interface.
"""

from app.core.services.dataset_status_service import DatasetStatusService
from app.core.services.mio_status_service import MioStatusService
from app.core.services.wf_exec_status_service import WfExecStatusService


class ServicesObjectsFactory:
    @staticmethod
    def get_dataset_status_service() -> DatasetStatusService:
        from app.core.services.impl.dataset_status_service_impl import DatasetStatusServiceImpl

        return DatasetStatusServiceImpl()

    @staticmethod
    def get_mio_status_service() -> MioStatusService:
        from app.core.services.impl.mio_status_service_impl import MioStatusServiceImpl

        return MioStatusServiceImpl()

    @staticmethod
    def get_wf_exec_status_service() -> WfExecStatusService:
        from app.core.services.impl.wf_exec_status_service_impl import WfExecStatusServiceImpl

        return WfExecStatusServiceImpl()
