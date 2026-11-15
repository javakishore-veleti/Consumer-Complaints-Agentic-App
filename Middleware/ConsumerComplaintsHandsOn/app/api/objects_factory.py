"""Builds the one FastAPI application for the whole project (one OpenAPI spec) and hands out the other singletons of
the api package (the callback secret check, D59; the status callback API, D60; the MIO status API, D61; and the
Airflow Variables upsert API, D42). The app is a singleton."""

import threading

from fastapi import Depends, FastAPI

from app.api.routers.airflow_upsert_secrets_api import AirflowUpsertSecretsApi
from app.api.routers.data_ingest_api import DataIngestApi
from app.api.routers.mio_status_api import MioStatusApi
from app.api.routers.wf_exec_callback_api import WfExecCallbackApi
from app.api.security.callback_secret_auth import CallbackSecretAuth


class ApiObjectsFactory:
    _app: FastAPI | None = None
    _lock = threading.Lock()

    @staticmethod
    def get_app() -> FastAPI:
        if ApiObjectsFactory._app is None:
            with ApiObjectsFactory._lock:
                if ApiObjectsFactory._app is None:
                    ApiObjectsFactory._app = ApiObjectsFactory._build_app()
        return ApiObjectsFactory._app

    @staticmethod
    def get_callback_secret_auth() -> CallbackSecretAuth:
        return CallbackSecretAuth()

    @staticmethod
    def get_wf_exec_callback_api() -> WfExecCallbackApi:
        return WfExecCallbackApi()

    @staticmethod
    def get_mio_status_api() -> MioStatusApi:
        return MioStatusApi()

    @staticmethod
    def get_airflow_upsert_secrets_api() -> AirflowUpsertSecretsApi:
        return AirflowUpsertSecretsApi()

    @staticmethod
    def _build_app() -> FastAPI:
        app = FastAPI(
            title="Consumer Complaints Hands-On API",
            version="0.1.0",
            description="Middleware API for the Consumer Complaints platform.",
        )
        app.include_router(DataIngestApi().router)
        # Portal endpoints stay open (no callback secret): the browser cannot keep a shared secret (D59, D61).
        app.include_router(ApiObjectsFactory.get_mio_status_api().router)
        # Every router an engine calls is protected as a whole by the callback secret (D59).
        app.include_router(
            ApiObjectsFactory.get_wf_exec_callback_api().router,
            dependencies=[Depends(ApiObjectsFactory.get_callback_secret_auth())],
        )
        app.include_router(
            ApiObjectsFactory.get_airflow_upsert_secrets_api().router,
            dependencies=[Depends(ApiObjectsFactory.get_callback_secret_auth())],
        )

        @app.get("/health", tags=["health"])
        def health() -> dict[str, str]:
            return {"status": "ok"}

        return app
