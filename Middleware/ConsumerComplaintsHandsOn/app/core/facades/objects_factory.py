"""The only module of the facades package that may import from facades/impl.

Static methods return the singleton, typed as the interface.
"""

from app.core.facades.data_ingest_facade import DataIngestFacade
from app.core.facades.mio_status_facade import MioStatusFacade
from app.core.facades.wf_exec_status_facade import WfExecStatusFacade


class FacadesObjectsFactory:
    @staticmethod
    def get_data_ingest_facade() -> DataIngestFacade:
        from app.core.facades.impl.data_ingest_facade_impl import DataIngestFacadeImpl

        return DataIngestFacadeImpl()

    @staticmethod
    def get_mio_status_facade() -> MioStatusFacade:
        from app.core.facades.impl.mio_status_facade_impl import MioStatusFacadeImpl

        return MioStatusFacadeImpl()

    @staticmethod
    def get_wf_exec_status_facade() -> WfExecStatusFacade:
        from app.core.facades.impl.wf_exec_status_facade_impl import WfExecStatusFacadeImpl

        return WfExecStatusFacadeImpl()
