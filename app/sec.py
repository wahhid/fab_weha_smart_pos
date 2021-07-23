from flask_appbuilder.security.sqla.manager import SecurityManager
from flask_appbuilder.security.views import UserInfoEditView, AuthDBView


class WehaAuthDBView(AuthDBView):
    login_template = "adminlte/weha_login_db.html"

class WehaSecurityManager(SecurityManager):
    authdbview = WehaAuthDBView