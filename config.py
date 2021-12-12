from redis import StrictRedis


class Config(object):
    # 项目配置
    DEBUG = True
    SECRET_KEY = "0BAbhFQnjElhzkd6+fhYRTl10YvEJ+pwEGIJEw419vTFVj0V+Uo0oL2w1TWEkDhE"

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


class DevelopmentConfig(Config):
    # 开发环境下的配置
    DEBUG = True


class ProductionConfig(Config):
    # 生产环境下的配置
    DEBUG = False


config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig
}

