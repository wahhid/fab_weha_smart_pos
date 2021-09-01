

from flask_appbuilder.models.sqla.interface import SQLAInterface
from flask_appbuilder.views import ModelView
from app.models import (PosConfig)
from app import appbuilder, db

class PosConfigView(ModelView):
    datamodel = SQLAInterface(PosConfig)
    list_columns = ["name", "is_multiple_payment"]

