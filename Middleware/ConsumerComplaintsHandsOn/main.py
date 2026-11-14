"""Entry point: uvicorn main:app  (run_local.sh migrates the database first)."""

from app.api.objects_factory import ApiObjectsFactory

app = ApiObjectsFactory.get_app()
