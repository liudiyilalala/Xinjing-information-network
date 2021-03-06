import logging
from logging.handlers import RotatingFileHandler
from flask import Flask
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect, generate_csrf
from redis import StrictRedis
from config import config
from flask import render_template
from flask import g


db = SQLAlchemy()
redis_store = None  # type: StrictRedis


def setup_log(config_name):
    # 设置日志的记录等级
    logging.basicConfig(level=config[config_name].LOGIN_LEVEL)  # 调试debug级
    # 创建日志记录器，指明日志保存的路径、每个日志文件的最大大小、保存的日志文件个数上限
    file_log_handler = RotatingFileHandler("logs/log", maxBytes=1024 * 1024 * 100, backupCount=10)
    # 创建日志记录的格式 日志等级 输入日志信息的文件名 行数 日志信息
    formatter = logging.Formatter('%(levelname)s %(filename)s:%(lineno)d %(message)s')
    # 为刚创建的日志记录器设置日志记录格式
    file_log_handler.setFormatter(formatter)
    # 为全局的日志工具对象（flask app使用的）添加日志记录器
    logging.getLogger().addHandler(file_log_handler)


# 定义创建app的函数，在manager函数内可以直接传参数即可，不用修改配置文件
def create_app(config_name):
    # 加载日志配置
    setup_log(config_name)
    # 创建flask对象
    app = Flask(__name__)
    # 加载配置
    app.config.from_object(config[config_name])
    # 初始化数据库
    db.init_app(app)
    # 初始化redis存储
    global redis_store
    redis_store = StrictRedis(host=config[config_name].REDIS_HOST, port=config[config_name].REDIS_PORT, decode_responses=True)
    # 开启CSRF保护
    CSRFProtect(app)
    # 初始化Session配置
    Session(app)

    @app.after_request
    def after_request(response):
        # 生成随机的csrf_token的值
        csrf_token = generate_csrf()
        # 设置一个cookie
        response.set_cookie("csrf_token", csrf_token)
        return response

    # 统一设置404页面
    from info.utils.common import user_login_data

    @app.errorhandler(404)
    @user_login_data
    def page_not_found(e):
        user = g.user
        data = {
            "user": user.to_dict() if user else None
        }
        return render_template("news/404.html", data=data)

    # 添加自定义过滤器
    from info.utils.common import do_index_class
    app.add_template_filter(do_index_class, "index_class")

    # 注册蓝图
    from info.modules.index import index_blu
    app.register_blueprint(index_blu)

    from info.modules.passport import passport_blu
    app.register_blueprint(passport_blu)

    from info.modules.news import news_blu
    app.register_blueprint(news_blu)

    from info.modules.profile import profile_blu
    app.register_blueprint(profile_blu)

    from info.modules.admin import admin_blu
    app.register_blueprint(admin_blu)

    return app

