from redis import StrictRedis
from flask import Flask, session
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import CSRFProtect
from flask_session import Session
from flask_script import Manager


class Config(object):
    # 项目配置
    DEBUG = True
    SECRET_KEY = "0BAbhFQnjElhzkd6/fhYRTl10YvEJ+pwEGIJEw419vTFVj0V+Uo0oL2w1TWEkDhE"

    # 为数据库添加配置
    SQLALCHEMY_DATABASE_URI = "mysql://root:123456@127.0.0.1:3306/information"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # 添加redis配置
    REDIS_HOST = "127.0.0.1"
    REDIS_PORT = 6379

    # Session保存配置
    # 设置session类型
    SESSION_TYPE = "redis"
    # 开启Session签名
    SESSION_USE_SIGNER = True
    # 指定Session保存的redis
    SESSION_REDIS = StrictRedis(host=REDIS_HOST, port=REDIS_PORT)
    # 设置需要过期
    SESSION_PERMANENT = False
    # 设置过期时间
    PERMANENT_SESSION_LIFETIME = 86400 * 2


app = Flask(__name__)
# 加载配置
app.config.from_object(Config)
# 初始化数据库
db = SQLAlchemy(app)
# 初始化redis存储
redis_store = StrictRedis(host=Config.REDIS_HOST, port=Config.REDIS_PORT)
# 开启CSRF保护
CSRFProtect(app)
# 初始化Session配置
Session(app)

manager = Manager(app)


@app.route('/')
def index():
    session["name"] = "123"
    return "index"


if __name__ == "__main__":
    manager.run()

