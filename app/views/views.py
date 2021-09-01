from flask.globals import session
from flask.signals import message_flashed
from app.api import PosOrderPaymentRestApi
from flask import render_template, redirect, make_response, flash
from flask_appbuilder.baseviews import BaseView
from flask_appbuilder.models.sqla import Model
from flask_appbuilder.models.sqla.interface import SQLAInterface
from flask_appbuilder.models.sqla.filters import FilterEqual, FilterEqualFunction, FilterStartsWith
from flask_appbuilder import ModelView, CompactCRUDMixin, MasterDetailView, expose
from flask_appbuilder.security.decorators import has_access
from flask_appbuilder.widgets import (
    ListWidget, ListBlock, ListItem, ListLinkWidget, ListThumbnail, ShowBlockWidget, ShowWidget
)
from sqlalchemy.sql.elements import Label
from sqlalchemy.sql.functions import func
from wtforms.fields import TextField
from flask_appbuilder.fieldwidgets import BS3TextFieldWidget
from flask_appbuilder.actions import action
from flask_appbuilder.views import get_filter_args
from app import appbuilder, db
from app.models import (
    Company, DocumentTemplate, IrSequence, PosCategory, PosConfig, PosFloor, PosOrder, PosOrderLine, PosPayment, PosPaymentMethod, PosSession, PosSessionLine, PosTable, ProductProduct, ResPartner
)

from random import randrange
import functools

def generate_12_random_numbers():
    numbers = [4,2,1]
    for x in range(9):
        numbers.append(randrange(10))
    return numbers

def calculate_checksum(ean):
    """
    Calculates the checksum for an EAN13
    @param list ean: List of 12 numbers for first part of EAN13
    :returns: The checksum for `ean`.
    :rtype: Integer
    """
    assert len(ean) == 12, "EAN must be a list of 12 numbers"
    sum_ = lambda x, y: int(x) + int(y)
    evensum = functools.reduce(sum_, ean[::2])
    oddsum = functools.reduce(sum_, ean[1::2])
    return (10 - ((evensum + oddsum * 3) % 10)) % 10

"""
    Create your Model based REST API::

    class MyModelApi(ModelRestApi):
        datamodel = SQLAInterface(MyModel)

    appbuilder.add_api(MyModelApi)

    Create your Views::

    class MyModelView(ModelView):
        datamodel = SQLAInterface(MyModel)


    Next, register your Views::


    appbuilder.add_view(
        MyModelView,
        "My View",
        icon="fa-folder-open-o",
        category="My Category",
        category_icon='fa-envelope'
    )
"""

"""
    Application wide 404 error handler
"""


@appbuilder.app.errorhandler(404)
def page_not_found(e):
    return (
        render_template(
            "404.html", base_template=appbuilder.base_template, appbuilder=appbuilder
        ),
        404,
    )


class BS3TextFieldROWidget(BS3TextFieldWidget):
    def __call__(self, field, **kwargs):
        kwargs['readonly'] = 'true'
        return super(BS3TextFieldROWidget, self).__call__(field, **kwargs)

class ListDownloadWidget(ListWidget):
    template = '/general/widgets/list_download.html'

class WehaWidgetList(ListWidget):

    template = '/general/widgets/list.html'

class WehaWidgetShow(ShowWidget):

    template = '/general/widgets/show.html'

class AdminLteModelView(ModelView):
    list_template = 'list.html'
    list_widget = WehaWidgetList
    can_delete = True

class IrSequenceModelView(ModelView):
    datamodel = SQLAInterface(IrSequence)

class DocumentTemplateModelView(ModelView):
    datamodel = SQLAInterface(DocumentTemplate)
    list_columns = ['code','name']

class CompanyModelView(ModelView):
    page_size = 5
    datamodel = SQLAInterface(Company)

class PosConfigView(ModelView):
    datamodel = SQLAInterface(PosConfig)
    list_columns = ["name", "is_multiple_payment"]

class PosCategoryView(ModelView):
    datamodel = SQLAInterface(PosCategory)

class ProductProductView(ModelView):
    datamodel = SQLAInterface(ProductProduct)
    list_columns = ["display_name", "pos_category", "lst_price","standard_price", "disc_price"]

    add_fieldsets = [
        (   "General Information", {
                "fields": [
                    "display_name", "pos_category", "barcode", "default_code"
                ]
            }
        ),
        (
            "Pricing", {
                "fields" : [
                    "lst_price", "standard_price"
                ]
            }
        )
    ]

class PosPaymentMethodView(ModelView):
    datamodel = SQLAInterface(PosPaymentMethod)

class PosSessionLineView(ModelView):
    datamodel = SQLAInterface(PosSessionLine)
    list_columns = ['pos_payment_method', 'amount_total']

class PosOrderInlineView(ModelView):
    datamodel = SQLAInterface(PosOrderLine)
    list_columns = ["name", "order", "qty", "price_unit", "price_subtotal"]

class PosPaymentView(ModelView):
    datamodel = SQLAInterface(PosPayment)
    list_columns = ["name", "amount"]
    can_create = False
    can_delete = False
    can_edit = False

class PosOrderView(ModelView):
    datamodel = SQLAInterface(PosOrder)
    list_columns = ["creation_date", "name", "pos_session", "amount_paid", "amount_total", "sync", "state"]
    related_views = [PosOrderInlineView, PosPaymentView]

    show_template = 'general/model/show_cascade.html'
    edit_template = 'appbuilder/general/model/edit_cascade.html'

class PosSessionView(ModelView):
    datamodel = SQLAInterface(PosSession)
    list_widget = ListDownloadWidget
    #base_filters = [['state', FilterEqual, 'open']]
    

    related_views = [PosOrderView, PosSessionLineView]
    show_template = 'general/model/show_cascade.html'
    edit_template = 'appbuilder/general/model/edit_cascade.html'

    label_columns = {'name': 'Name', 'session_date': 'Date', 'config': 'Config'}
    list_columns = ['name', 'session_date', 'config', 'user', 'state']
    search_columns = ['name', 'session_date', 'config', 'state']
    edit_form_extra_fields = {
        'creation_date': TextField('Creation Date',widget=BS3TextFieldROWidget()),
        'state': TextField('State',widget=BS3TextFieldROWidget())
    }

    @action("close_session",
            "Close Session",
            "Do you really want to close session?",
            multiple=False)
    def close_session(self, sessions):
        #Check Unpaid Pos Order

        # posOrders = db.session.query(PosOrder).filter(PosOrder.pos_session_id==sessions.id).all()
        # if len(posOrders) > 0:
        #     flash(f'Cannot close session {sessions.name} because 1 or more unpaid pos order')
        #     return redirect(self.get_redirect())

        if isinstance(sessions, list):
            for session in sessions:
                #contact.name = contact.name.capitalize()
                #self.datamodel.edit(contact)
                session.state = 'paid'
                self.datamodel.edit(session)
                self.update_redirect()      
        else:
            #contacts.name = contacts.name.capitalize()
            sessions.state = 'paid'
            self.datamodel.edit(sessions)

        return redirect(self.get_redirect())
    
   

    @action("compute_summary",
            "Compute Summary",
            "Do you to calculate summary?",
            multiple=False)
    def compute_summary(self, sessions):
        #Delete Current Payment Line
        db.session.query(PosSessionLine).filter(PosSessionLine.pos_session_id==sessions.id).delete()
        db.session.commit()

        payments = db.session.query(
            Label('name',  PosPayment.name),
            Label('payment_method_id', PosPayment.payment_method_id),
            Label('amount_total',func.sum(PosPayment.amount))
        ).join(PosOrder).group_by(PosPayment.payment_method_id).filter(PosOrder.pos_session_id==sessions.id).all()

        amount_total = 0.0
        for row in payments:
            posSessionLine = PosSessionLine()
            posSessionLine.pos_session_id = sessions.id
            posSessionLine.payment_method_id = row.payment_method_id
            print(row.payment_method_id)
            posSessionLine.amount_total = row.amount_total
            amount_total += row.amount_total
            #Create POS Session Line
            db.session.add(posSessionLine)
            db.session.commit()

        sessions.amount_total = amount_total
        self.datamodel.edit(sessions)
        flash(f'Session {sessions.name} Compute Summary Successfully',"info")
        return redirect(self.get_redirect())
    
    @expose('/csv', methods=['GET'])
    def download_csv(self):
        get_filter_args(self._filters)
        #order_column, order_direction = self.base_order
        #count, lst = self.datamodel.query(self._filters, order_column, order_direction)
        count, lst = self.datamodel.query(self._filters)
        csv = ''
        for item in self.datamodel.get_values(lst, self.list_columns):
            csv += str(item) + '\n'
        response = make_response(csv)
        cd = 'attachment; filename=mycsv.csv'
        response.headers['Content-Disposition'] = cd
        response.mimetype='text/csv'
        return response

    @expose('/zreport', methods=['GET'])
    def download_zreport(self):
        get_filter_args(self._filters)
        #order_column, order_direction = self.base_order
        #count, lst = self.datamodel.query(self._filters, order_column, order_direction)
        count, lst = self.datamodel.query(self._filters)
        csv = ''
        for item in self.datamodel.get_values(lst, self.list_columns):
            csv += str(item) + '\n'
        response = make_response(csv)
        cd = 'attachment; filename=mycsv.csv'
        response.headers['Content-Disposition'] = cd
        response.mimetype='text/csv'
        return response

class PosTableView(ModelView):
    datamodel = SQLAInterface(PosTable)
    list_columns = ['name', 'capacity']

class PosFloorView(ModelView):
    datamodel = SQLAInterface(PosFloor)
    list_columns = ['name']

class ResPartnerView(ModelView):
    datamodel = SQLAInterface(ResPartner)
    list_title = 'Customer'
    show_title = 'Customer'
    add_title = 'Create Customer'
    list_columns = ['name', 'barcode', 'type', 'phone', 'mobile']    

    def pre_add(self, item):
        numbers = generate_12_random_numbers()
        numbers.append(calculate_checksum(numbers))
        item.barcode = ''.join(map(str, numbers))
        return super().pre_add(item)
        
class DocumentReportView(BaseView):
    route_base = "/document"

    @expose("/report/pos_detail/<string:trans_date>")
    def report_pos_detail(self, trans_date):
        # do something with param1
        # and return to previous page or index
        param1 = """
        <div class="container">
  <div class="card">
<div class="card-header">
Invoice
<strong>01/01/01/2018</strong> 
  <span class="float-right"> <strong>Status:</strong> Pending</span>

</div>
<div class="card-body">
<div class="row mb-4">
<div class="col-sm-6">
<h6 class="mb-3">From:</h6>
<div>
<strong>Webz Poland</strong>
</div>
<div>Madalinskiego 8</div>
<div>71-101 Szczecin, Poland</div>
<div>Email: info@webz.com.pl</div>
<div>Phone: +48 444 666 3333</div>
</div>

<div class="col-sm-6">
<h6 class="mb-3">To:</h6>
<div>
<strong>Bob Mart</strong>
</div>
<div>Attn: Daniel Marek</div>
<div>43-190 Mikolow, Poland</div>
<div>Email: marek@daniel.com</div>
<div>Phone: +48 123 456 789</div>
</div>



</div>

<div class="table-responsive-sm">
<table class="table table-striped">
<thead>
<tr>
<th class="center">#</th>
<th>Item</th>
<th>Description</th>

<th class="right">Unit Cost</th>
  <th class="center">Qty</th>
<th class="right">Total</th>
</tr>
</thead>
<tbody>
<tr>
<td class="center">1</td>
<td class="left strong">Origin License</td>
<td class="left">Extended License</td>

<td class="right">$999,00</td>
  <td class="center">1</td>
<td class="right">$999,00</td>
</tr>
<tr>
<td class="center">2</td>
<td class="left">Custom Services</td>
<td class="left">Instalation and Customization (cost per hour)</td>

<td class="right">$150,00</td>
  <td class="center">20</td>
<td class="right">$3.000,00</td>
</tr>
<tr>
<td class="center">3</td>
<td class="left">Hosting</td>
<td class="left">1 year subcription</td>

<td class="right">$499,00</td>
  <td class="center">1</td>
<td class="right">$499,00</td>
</tr>
<tr>
<td class="center">4</td>
<td class="left">Platinum Support</td>
<td class="left">1 year subcription 24/7</td>

<td class="right">$3.999,00</td>
  <td class="center">1</td>
<td class="right">$3.999,00</td>
</tr>
</tbody>
</table>
</div>
<div class="row">
<div class="col-lg-4 col-sm-5">

</div>

<div class="col-lg-4 col-sm-5 ml-auto">
<table class="table table-clear">
<tbody>
<tr>
<td class="left">
<strong>Subtotal</strong>
</td>
<td class="right">$8.497,00</td>
</tr>
<tr>
<td class="left">
<strong>Discount (20%)</strong>
</td>
<td class="right">$1,699,40</td>
</tr>
<tr>
<td class="left">
 <strong>VAT (10%)</strong>
</td>
<td class="right">$679,76</td>
</tr>
<tr>
<td class="left">
<strong>Total</strong>
</td>
<td class="right">
<strong>$7.477,36</strong>
</td>
</tr>
</tbody>
</table>

</div>

</div>

</div>
</div>
</div>
"""
        return param1

db.create_all()

appbuilder.add_view(CompanyModelView, "Companys", icon="fa-folder-open-o", category="Settings")
appbuilder.add_view(IrSequenceModelView, "Sequences", icon="fa-folder-open-o", category="Settings")
appbuilder.add_view(DocumentTemplateModelView, "Templates", icon="fa-folder-open-o", category="Settings")
appbuilder.add_view(PosConfigView, "Config", icon="fa-envelope", category="Master")
appbuilder.add_view(PosCategoryView, "Categories", icon="fa-envelope", category="Master")
appbuilder.add_view(ProductProductView, "Products", icon="fa-envelope", category="Master")
appbuilder.add_view(ResPartnerView, "Customers", icon="fa-envelope", category="Master")
appbuilder.add_view(PosPaymentMethodView, "Payment Method", icon="fa-envelope", category="Master")
appbuilder.add_view(PosTableView, "Tables", icon="fa-envelope", category="Master")
appbuilder.add_view(PosFloorView, "Floors", icon="fa-envelope", category="Master")
appbuilder.add_view(PosSessionView, "Session", icon="fa-envelope", category="Transaction")
appbuilder.add_view(PosSessionLineView, "Session", icon="fa-envelope", category="Transaction")
appbuilder.add_view(PosOrderView, "Order", icon="fa-envelope", category="Transaction")
appbuilder.add_view(PosOrderInlineView, "Order Line", icon="fa-envelope", category="Transaction")
appbuilder.add_view(PosPaymentView, "Order Payment", icon="fa-envelope", category="Transaction")

appbuilder.add_view_no_menu(DocumentReportView())