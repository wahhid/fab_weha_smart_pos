
import json
from operator import pos
from os import access
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
from . import appbuilder, celery, db, models
from flask_login import current_user
from jinja2 import Template
from datetime import datetime
import requests


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
    show_columns = ['name','pos_session_id', 'partner', 'total_orderline', 'total_paymentline', 'total_item', 'state']
    list_columns = ['name','pos_session_id', 'partner', 'total_orderline', 'total_paymentline', 'total_item', 'state']
    search_columns = ['pos_session_id', 'user_id', 'state']

    #@celery.task()
    def upload_transaction(self, pos_order_id): 
        try:
            pos_order = db.session.query(models.PosOrder).get(pos_order_id)
            pos_order_sync = {
                "name": pos_order.name,
                "user_id": pos_order.user.id,
                "date_order": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                #"smart_pos_session_id": pos_order.pos_session.id,
                "smart_pos_session_id": {
                    "id": pos_order.pos_session.id,
                    "name": pos_order.pos_session.name,
                    "session_date": pos_order.pos_session.session_date.strftime('%Y-%m-%d'),
                    "date_open": "2021-08-06 07:30:00",
                    "config_id": {
                        "id": pos_order.pos_session.config.id,
                        "name": pos_order.pos_session.config.name,
                        "code": pos_order.pos_session.config.code
                }
                },
                "amount_total": pos_order.amount_total,
                "amount_paid": pos_order.amount_paid,
                "state": pos_order.state,
            }
            smart_pos_order_line_ids = []
            pos_order_lines = db.session.query(models.PosOrderLine).filter_by(order_id=pos_order.id).all()
            for pos_order_line in pos_order_lines:
                value = {
                    "description": pos_order_line.name,
                    "product_id": pos_order_line.product.id,
                    "qty": pos_order_line.qty,
                    "price_unit": pos_order_line.price_unit,
                    "tax_id": False,
                    "amount_tax": 0,
                    "amount_discount": 0,
                    "amount_total": pos_order_line.price_subtotal
                }
                smart_pos_order_line_ids.append(value)

            pos_order_sync.update({'smart_pos_order_line_ids':smart_pos_order_line_ids})

            smart_pos_order_payment_ids = []
            pos_order_payments = db.session.query(models.PosPayment).filter_by(pos_order_id=pos_order.id).all()
            for pos_order_payment in pos_order_payments:
                value = {
                    "smart_pos_payment_method_id": pos_order_payment.pos_payment_method.id,
                    "discount_in_percentage": 0.0,
                    "amount_discount": 0.0,
                    "amount_total": pos_order_payment.amount
                }
                smart_pos_order_payment_ids.append(value)
            pos_order_sync.update({'smart_pos_order_payment_ids':smart_pos_order_payment_ids})
            print(json.dumps(pos_order_sync))
            
            url = "http://smart-pos-dev.server002.weha-id.com/api/auth/token?db=smart-pos-dev&login=admin&password=P@ssw0rd"
            payload={}
            headers={}
            response = requests.request("GET", url, headers=headers)
            if response.status_code == 200:
                response_json = response.json()
                access_token = response_json['access_token']
                headers = {
                    'Content-Type': 'application/json',
                    'access-token': access_token,
                }
                payload=json.dumps(pos_order_sync)
                url = "http://smart-pos-dev.server002.weha-id.com/api/smartpos/v1.0/uploadtransaction"
                response = requests.request("POST", url, headers=headers, data=payload)
                if response.status_code == 200:
                    print("Upload Transaction Successfully")
                    response_json = response.json()
                    result = response_json['result']
                    print(result)
                    if not result['err']:
                        pos_order.sync = True 
                        db.session.commit()
                else:
                    print(response.json())
            else:
                print(response.json())
        except Exception as e:
            print(e)

    def post_update(self, item):
        res = super().post_update(item)
        #Upload Transaction
        if item.state == 'paid':
            print("Odoo - Upload Transaction")
            #result = self.upload_transaction.delay(item.id)
            #result.wait()
            self.upload_transaction(item.id)
        return res

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

class ResPartnerRestApi(ModelRestApi):
    resource_name = "res_partner"
    datamodel = SQLAInterface(models.ResPartner)

class PosTableRestApi(ModelRestApi):
    resource_name = "pos_table"
    datamodel = SQLAInterface(models.PosTable)


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
appbuilder.add_api(ResPartnerRestApi)
appbuilder.add_api(PosTableRestApi)