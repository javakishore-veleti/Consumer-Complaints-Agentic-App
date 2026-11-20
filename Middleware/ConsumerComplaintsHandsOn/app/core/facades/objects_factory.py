"""The only module of the facades package that may import from facades/impl.

Static methods return the singleton, typed as the interface.
"""

import threading

from app.core.common.bean_registry import bean_registry
from app.core.facades.airflow_start_dag_facade import AirflowStartDagFacade
from app.core.facades.airflow_upsert_secrets_facade import AirflowUpsertSecretsFacade
from app.core.facades.app_endpoint_list_facade import AppEndpointListFacade
from app.core.facades.dag_context_facade import DagContextFacade
from app.core.facades.dataset_import_run_facade import DatasetImportRunFacade
from app.core.facades.intellect_query_facade import IntellectQueryFacade
from app.core.facades.mio_status_facade import MioStatusFacade
from app.core.facades.query_ast_facade import QueryAstFacade
from app.core.facades.risk_radar_facade import RiskRadarFacade
from app.core.facades.start_wf_facade import StartWfFacade
from app.core.facades.wf_exec_status_facade import WfExecStatusFacade
from app.core.facades.wf_list_facade import WfListFacade
from app.core.facades.workflow_logs_facade import WorkflowLogsFacade
from app.core.facades.zone_ingest_log_facade import ZoneIngestLogFacade


class FacadesObjectsFactory:
    _initialized = False
    _lock = threading.RLock()

    @staticmethod
    def init() -> None:
        if FacadesObjectsFactory._initialized:
            return
        with FacadesObjectsFactory._lock:
            if FacadesObjectsFactory._initialized:
                return
            from app.core.facades.impl.af_start.airflow_start_dag_facade_impl import (
                AirflowStartDagFacadeImpl,
            )
            from app.core.facades.impl.airflow_upsert_secrets_facade_impl import (
                AirflowUpsertSecretsFacadeImpl,
            )
            from app.core.facades.impl.app_ep.app_endpoint_list_facade_impl import (
                AppEndpointListFacadeImpl,
            )
            from app.core.facades.impl.dag_context.dag_context_facade_impl import (
                DagContextFacadeImpl,
            )
            from app.core.facades.impl.dataset_import_run_facade_impl import (
                DatasetImportRunFacadeImpl,
            )
            from app.core.facades.impl.intellect.intellect_query_facade_impl import (
                IntellectQueryFacadeImpl,
            )
            from app.core.facades.impl.intellect.query_ast_facade_impl import (
                QueryAstFacadeImpl,
            )
            from app.core.facades.impl.intellect.risk_radar_facade_impl import (
                RiskRadarFacadeImpl,
            )
            from app.core.facades.impl.mio_status_facade_impl import MioStatusFacadeImpl
            from app.core.facades.impl.start_wf.start_wf_facade_impl import (
                StartWfFacadeImpl,
            )
            from app.core.facades.impl.wf_exec_status_facade_impl import (
                WfExecStatusFacadeImpl,
            )
            from app.core.facades.impl.wf_list.wf_list_facade_impl import (
                WfListFacadeImpl,
            )
            from app.core.facades.impl.workflow_logs_facade_impl import (
                WorkflowLogsFacadeImpl,
            )
            from app.core.facades.impl.zone_ingest_log_facade_impl import (
                ZoneIngestLogFacadeImpl,
            )

            bean_registry.register(MioStatusFacade, MioStatusFacadeImpl())
            bean_registry.register(WfExecStatusFacade, WfExecStatusFacadeImpl())
            bean_registry.register(AirflowUpsertSecretsFacade, AirflowUpsertSecretsFacadeImpl())
            bean_registry.register(WfListFacade, WfListFacadeImpl())
            bean_registry.register(AppEndpointListFacade, AppEndpointListFacadeImpl())
            bean_registry.register(AirflowStartDagFacade, AirflowStartDagFacadeImpl())
            bean_registry.register(StartWfFacade, StartWfFacadeImpl())
            bean_registry.register(IntellectQueryFacade, IntellectQueryFacadeImpl())
            bean_registry.register(QueryAstFacade, QueryAstFacadeImpl())
            bean_registry.register(RiskRadarFacade, RiskRadarFacadeImpl())
            bean_registry.register(DatasetImportRunFacade, DatasetImportRunFacadeImpl())
            bean_registry.register(DagContextFacade, DagContextFacadeImpl())
            bean_registry.register(ZoneIngestLogFacade, ZoneIngestLogFacadeImpl())
            bean_registry.register(WorkflowLogsFacade, WorkflowLogsFacadeImpl())
            FacadesObjectsFactory._initialized = True

    @staticmethod
    def get_mio_status_facade() -> MioStatusFacade:
        FacadesObjectsFactory.init()
        return bean_registry.get_one(MioStatusFacade)  # type: ignore[return-value]

    @staticmethod
    def get_wf_exec_status_facade() -> WfExecStatusFacade:
        FacadesObjectsFactory.init()
        return bean_registry.get_one(WfExecStatusFacade)  # type: ignore[return-value]

    @staticmethod
    def get_airflow_upsert_secrets_facade() -> AirflowUpsertSecretsFacade:
        FacadesObjectsFactory.init()
        return bean_registry.get_one(AirflowUpsertSecretsFacade)  # type: ignore[return-value]

    @staticmethod
    def get_wf_list_facade() -> WfListFacade:
        FacadesObjectsFactory.init()
        return bean_registry.get_one(WfListFacade)  # type: ignore[return-value]

    @staticmethod
    def get_app_endpoint_list_facade() -> AppEndpointListFacade:
        FacadesObjectsFactory.init()
        return bean_registry.get_one(AppEndpointListFacade)  # type: ignore[return-value]

    @staticmethod
    def get_airflow_start_dag_facade() -> AirflowStartDagFacade:
        FacadesObjectsFactory.init()
        return bean_registry.get_one(AirflowStartDagFacade)  # type: ignore[return-value]

    @staticmethod
    def get_start_wf_facade() -> StartWfFacade:
        FacadesObjectsFactory.init()
        return bean_registry.get_one(StartWfFacade)  # type: ignore[return-value]

    @staticmethod
    def get_intellect_query_facade() -> IntellectQueryFacade:
        FacadesObjectsFactory.init()
        return bean_registry.get_one(IntellectQueryFacade)  # type: ignore[return-value]

    @staticmethod
    def get_query_ast_facade() -> QueryAstFacade:
        FacadesObjectsFactory.init()
        return bean_registry.get_one(QueryAstFacade)  # type: ignore[return-value]

    @staticmethod
    def get_risk_radar_facade() -> RiskRadarFacade:
        FacadesObjectsFactory.init()
        return bean_registry.get_one(RiskRadarFacade)  # type: ignore[return-value]

    @staticmethod
    def get_dataset_import_run_facade() -> DatasetImportRunFacade:
        FacadesObjectsFactory.init()
        return bean_registry.get_one(DatasetImportRunFacade)  # type: ignore[return-value]

    @staticmethod
    def get_dag_context_facade() -> DagContextFacade:
        FacadesObjectsFactory.init()
        return bean_registry.get_one(DagContextFacade)  # type: ignore[return-value]

    @staticmethod
    def get_zone_ingest_log_facade() -> ZoneIngestLogFacade:
        FacadesObjectsFactory.init()
        return bean_registry.get_one(ZoneIngestLogFacade)  # type: ignore[return-value]

    @staticmethod
    def get_workflow_logs_facade() -> WorkflowLogsFacade:
        FacadesObjectsFactory.init()
        return bean_registry.get_one(WorkflowLogsFacade)  # type: ignore[return-value]
