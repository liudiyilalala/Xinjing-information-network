from . import index_blu
from flask import render_template
from flask import current_app
from flask import session

from ...models import User


@index_blu.route('/')
def index():
    # 页面右上角是否登陆功能实现
    # 取出用户id
    user_id = session.get("user_id", None)
    # 如果用户id存在，尝试从数据库中取出用户模型
    user = None
    if user_id:
        try:
            user = User.query.get(user_id)
        except Exception as e:
            current_app.logger.error(e)

    # 如果取出用户模型，将用户模型保存返回前端
    data = {
        "user": user.to_dict() if user else None
    }

    return render_template('news/index.html', data=data)


# 加载favicon.ico图标
@index_blu.route('/favicon.ico')
def favicon():
    return current_app.send_static_file('news/favicon.ico')

