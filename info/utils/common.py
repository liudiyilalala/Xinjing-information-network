import functools

from flask import session
from flask import current_app
from info.models import User
from flask import g


def do_index_class(index):
    """自定义过滤器，过滤点击排行的class属性"""
    if index == 0:
        return "first"
    elif index == 1:
        return "second"
    elif index == 2:
        return "third"
    else:
        return ""


# 定义装饰器，使用装饰器来抽取用户登陆
def user_login_data(fun):
    @functools.wraps(fun)
    def wrapper(*args, **kwargs):
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
        # 把查询出来的数据赋值给g变量
        g.user = user
        return fun(*args, **kwargs)
    return wrapper

