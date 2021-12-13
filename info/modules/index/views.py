from . import index_blu
from flask import render_template
from flask import current_app


@index_blu.route('/')
def index():
    return render_template('news/index.html')


# 加载favicon.ico图标
@index_blu.route('/favicon.ico')
def favicon():
    return current_app.send_static_file('news/favicon.ico')

