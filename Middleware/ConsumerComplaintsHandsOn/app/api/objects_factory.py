"""Builds the one FastAPI application for the whole project (one OpenAPI spec). The app is a singleton."""

import threading

from fastapi import FastAPI

from app.api.routers.data_ingest_router import router as data_ingest_router


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
    def _build_app() -> FastAPI:
        app = FastAPI(
            title="Consumer Complaints Hands-On API",
            version="0.1.0",
            description="Middleware API for the Consumer Complaints platform.",
        )
        app.include_router(data_ingest_router)

        @app.get("/health", tags=["health"])
        def health() -> dict[str, str]:
            return {"status": "ok"}

        return app
