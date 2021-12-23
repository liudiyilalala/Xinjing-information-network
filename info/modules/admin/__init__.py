# 新闻后台中心视图展示
from flask import Blueprint
from flask import session
from flask import request
from flask import url_for, redirect


admin_blu = Blueprint("admin", __name__, url_prefix="/admin")  # url前加passport
from . import views


# 后台访问权限控制，非管理员用户不能进入新闻后台页面.并在首页退出功能中将session中的is_admin删除掉
# 使用请求勾子实现,在请求之前校验
@admin_blu.before_request
def check_admin():
    # 如果is_admin是false，并且要访问的页面不是新闻后台登陆页面，就重定向到首页
    is_admin = session.get('is_admin', False)
    if not is_admin and not request.url.endswith(url_for("admin.login")):
        return redirect('/')

