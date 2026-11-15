"""Entry point: uvicorn main:app  (run_app.sh start migrates the database first)."""

from app.api.objects_factory import ApiObjectsFactory
from app.core.dao.objects_factory import DaoObjectsFactory
from app.core.facades.objects_factory import FacadesObjectsFactory
from app.core.services.objects_factory import ServicesObjectsFactory

DaoObjectsFactory.init()
ServicesObjectsFactory.init()
FacadesObjectsFactory.init()
ApiObjectsFactory.init()

app = ApiObjectsFactory.get_app()
