from flask_appbuilder import IndexView


class WehaIndexView(IndexView):
    index_template = 'weha_index.html'