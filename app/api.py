
import json
from flask_appbuilder.const import API_RESULT_RES_KEY
from flask_appbuilder.models.sqla import Model
from marshmallow.decorators import post_dump
from sqlalchemy.sql import func
from flask import g, request, jsonify
from flask_appbuilder.api import ModelRestApi, BaseApi, expose, rison, safe
from flask_appbuilder.security.decorators import protect
from flask_appbuilder.security.sqla.models import User
from flask_appbuilder.models.sqla.interface import SQLAInterface
from sqlalchemy.sql.functions import user
from . import appbuilder, db, models
from flask_login import current_user
from jinja2 import Template
from datetime import datetime



def get_user_id():
    try:
        return g.user.id
    except Exception:
        return None

def get_user():
    try:
        return g.user
    except Exception:
        return None

class PosApi(BaseApi):

    resource_name = "user_pos"

    @expose("/get_user_id")
    @protect()
    def get_user_id(self):
      user_id = get_user_id()
      print(user_id)
      return self.response(200, data={'user_id': user_id})


    @expose("/get_user")
    @protect()
    def get_user(self):
      print(current_user.__getattr__)
      user = get_user()
      print(user)
      return self.response(200, data={"user": str(user)})

class DocumentApi(BaseApi):
    @expose("/report/template/<code>")
    @protect()
    def render(self, code):
        template = Template(f)
        document_template = db.session.query(models.DocumentTemplate).filter_by(code=code).first()

        return self.response(200, data={})


class PosCategoryRestApi(ModelRestApi):
    resource_name = 'pos_category'
    datamodel = SQLAInterface(models.PosCategory)
    
class ProductProductRestApi(ModelRestApi):
    resource_name = "product"
    datamodel = SQLAInterface(models.ProductProduct)

class PosConfigRestApi(ModelRestApi):
    resource_name = "pos_config"
    datamodel = SQLAInterface(models.PosConfig)

class PosSessionRestApi(ModelRestApi):
    resource_name = "pos_session"
    datamodel = SQLAInterface(models.PosSession)
    search_columns = ['company_id','config_id','user_id','state']
    
    def pre_add(self, item):
        ir_sequence = db.session.query(models.IrSequence).filter_by(name='POS Session Sequence').first()
        name = ir_sequence.get_next_number_by_name()
        item.name = name
        return super().pre_add(item)
    
    
    @expose("/active", methods=["GET"])
    @rison()
    def active(self, **kwargs):
        print(kwargs)
        config_id = kwargs['rison']['config_id']
        user_id = kwargs['rison']['user_id']
        pos_session= db.session.query(models.PosSession).filter_by(config_id=config_id, user_id=user_id, state='open').first()
        if pos_session:
            result = self.list_model_schema.dump(pos_session,many=False)
            result.update({'id':self.datamodel.get_pk_value(pos_session)})
            return self.response(
                200,
                **{
                    API_RESULT_RES_KEY: result,
                },
            )
        else:
            # #Create POS Order
            pos_session = models.PosSession()
            pos_session.config_id = config_id
            pos_session.user_id = user_id
            pos_session.state = 'open' 
            self.pre_add(pos_session)
            self.datamodel.add(pos_session)
            self.post_add(pos_session)
            #pos_order = self.datamodel.get(self.datamodel.get_pk)
            result = self.add_model_schema.dump(pos_session,many=False)
            result.update({'id':self.datamodel.get_pk_value(pos_session)})
            return self.response(
                201,
                **{
                    API_RESULT_RES_KEY: result,
                },
            )

class PosOrderRestApi(ModelRestApi):
    resource_name = "pos_order"
    datamodel = SQLAInterface(models.PosOrder)
    show_columns = ['name','pos_session_id','total_orderline', 'total_paymentline', 'total_item', 'state']
    list_columns = ['name','pos_session_id','total_orderline', 'total_paymentline', 'total_item', 'state']
    search_columns = ['pos_session_id', 'user_id', 'state']


    def pre_add(self, item):
        ir_sequence = db.session.query(models.IrSequence).filter_by(name='POS Order Sequence').first()
        name = ir_sequence.get_next_number_by_name()
        item.name = name
        return super().pre_add(item)

    @expose("/active", methods=["GET"])
    @rison()
    def active(self, **kwargs):
        print(kwargs)
        pos_session_id = kwargs['rison']['pos_session_id']
        user_id = kwargs['rison']['user_id']
        pos_order= db.session.query(models.PosOrder).filter_by(pos_session_id=pos_session_id, user_id=user_id, state='unpaid').first()
        if pos_order:
            result = self.list_model_schema.dump(pos_order,many=False)
            result.update({'id': self.datamodel.get_pk_value(pos_order)})
            return self.response(
                200,
                **{
                    API_RESULT_RES_KEY: result,
                },
            )
        else:
            # #Create POS Order
            pos_order = models.PosOrder()
            pos_order.pos_session_id = pos_session_id
            pos_order.user_id = user_id
            pos_order.creation_date = datetime.now()
            pos_order.state = 'unpaid' 
            self.pre_add(pos_order)
            self.datamodel.add(pos_order)
            self.post_add(pos_order)
            #pos_order = self.datamodel.get(self.datamodel.get_pk)
            result = self.add_model_schema.dump(pos_order,many=False)
            result.update({'id': self.datamodel.get_pk_value(pos_order)})
            return self.response(
                201,
                **{
                    API_RESULT_RES_KEY: result,
                },
            )

    @expose("/report/render", methods=["GET"])
    @rison()
    def render(self, **kwargs):
        print(kwargs)
        pos_order_id = kwargs['rison']['id']
        code = kwargs['rison']['code']
        document_template = db.session.query(models.DocumentTemplate).filter_by(code=code).first()
        template = Template(document_template.templ)
        pos_order_lines = db.session.query(models.PosOrderLine).filter_by(order_id=pos_order_id)
        content = {
            'pos_order_lines': pos_order_lines
        }
        #Generate Jinja Template
        data  = template.render(content)
        #Save Jinja Template to POS Order
        pos_order = db.session.query(models.PosOrder).get(pos_order_id)
        pos_order.receipt_doc = data
        db.session.commit()
        return self.response(200, result=data)

class PosOrderLineRestApi(ModelRestApi):
    resource_name = "pos_order_line"
    datamodel = SQLAInterface(models.PosOrderLine)
    search_columns = ['order_id']
    page_size = 1000

class PosOrderPaymentRestApi(ModelRestApi):
    resource_name = "pos_order_payment"
    datamodel = SQLAInterface(models.PosPayment)
    search_columns = ['pos_order_id']
    page_size = 1000

class AbUserRestApi(ModelRestApi):
    resource_name = "abuser"
    datamodel = SQLAInterface(User)
    show_columns = ['username','roles']    
    search_columns = ['username']

class DocumentTemplateRestApi(ModelRestApi):
    resource_name = "document_template"
    datamodel = SQLAInterface(models.DocumentTemplate)

appbuilder.add_api(DocumentTemplateRestApi)
appbuilder.add_api(PosApi)
appbuilder.add_api(PosCategoryRestApi)
appbuilder.add_api(ProductProductRestApi)
appbuilder.add_api(PosConfigRestApi)
appbuilder.add_api(PosSessionRestApi)
appbuilder.add_api(PosOrderRestApi)
appbuilder.add_api(PosOrderLineRestApi)
appbuilder.add_api(PosOrderPaymentRestApi)
appbuilder.add_api(AbUserRestApi)

