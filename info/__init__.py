from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config import config
from redis import StrictRedis
from flask_wtf.csrf import CSRFProtect
from flask_session import Session


db = SQLAlchemy()


# 定义创建app的函数，在manager函数内可以直接传参数即可，不用修改配置文件
def create_app(config_name):
    app = Flask(__name__)
    # 加载配置
    app.config.from_object(config[config_name])
    # 初始化数据库
    db.init_app(app)
    # 初始化redis存储
    redis_store = StrictRedis(host=config[config_name].REDIS_HOST, port=config[config_name].REDIS_PORT)
    # 开启CSRF保护
    CSRFProtect(app)
    # 初始化Session配置
    Session(app)

    return app

