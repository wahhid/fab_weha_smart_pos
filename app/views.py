from flask import render_template, redirect, make_response
from flask_appbuilder.baseviews import BaseView
from flask_appbuilder.models.sqla import Model
from flask_appbuilder.models.sqla.interface import SQLAInterface
from flask_appbuilder import ModelView, CompactCRUDMixin, MasterDetailView, expose
from flask_appbuilder.security.decorators import has_access
from flask_appbuilder.widgets import (
    ListWidget, ListBlock, ListItem, ListLinkWidget, ListThumbnail, ShowBlockWidget, ShowWidget
)
from wtforms.fields import TextField
from flask_appbuilder.fieldwidgets import BS3TextFieldWidget
from flask_appbuilder.actions import action
from flask_appbuilder.views import get_filter_args
from . import appbuilder, db
from . models import (
    Company, DocumentTemplate, IrSequence, PosCategory, PosConfig, PosOrder, PosOrderLine, PosPayment, PosPaymentMethod, PosSession, ProductProduct
)

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

class PosConfigView(ModelView):
    datamodel = SQLAInterface(PosConfig)
    list_columns = ["name", "is_multiple_payment"]

class PosSessionView(ModelView):
    datamodel = SQLAInterface(PosSession)
    list_widget = ListDownloadWidget
    list_columns = ['name', 'config', 'user', 'state']
    search_columns = ['name','config', 'state']
    edit_form_extra_fields = {
        'creation_date': TextField('Creation Date',widget=BS3TextFieldROWidget()),
        'state': TextField('State',widget=BS3TextFieldROWidget())
    }

    @action("close_session",
            "Close Session",
            "Do you really want to close session?")
    def close_session(self, sessions):
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
    list_columns = ["creation_date", "name", "pos_session", "amount_paid", "amount_total", "state"]
    related_views = [PosOrderInlineView, PosPaymentView]

    show_template = 'general/model/show_cascade.html'
    edit_template = 'appbuilder/general/model/edit_cascade.html'

db.create_all()

appbuilder.add_view(CompanyModelView, "Companys", icon="fa-folder-open-o", category="Settings")
appbuilder.add_view(IrSequenceModelView, "Sequences", icon="fa-folder-open-o", category="Settings")
appbuilder.add_view(DocumentTemplateModelView, "Templates", icon="fa-folder-open-o", category="Settings")
appbuilder.add_view(PosCategoryView, "Categories", icon="fa-envelope", category="Master")
appbuilder.add_view(ProductProductView, "Products", icon="fa-envelope", category="Master")
appbuilder.add_view(PosPaymentMethodView, "Payment Method", icon="fa-envelope", category="Master")
appbuilder.add_view(PosConfigView, "Config", icon="fa-envelope", category="Master")
appbuilder.add_view(PosSessionView, "Session", icon="fa-envelope", category="Transaction")
appbuilder.add_view(PosOrderView, "Order", icon="fa-envelope", category="Transaction")
appbuilder.add_view(PosOrderInlineView, "Order Line", icon="fa-envelope", category="Transaction")
appbuilder.add_view(PosPaymentView, "Order Payment", icon="fa-envelope", category="Transaction")