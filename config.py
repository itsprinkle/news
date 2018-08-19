import logging

import redis
#配置信息类
class Config(object):

    #开启默认的调试模式
    DEBUG = True

    #设置SECRET_KEY
    SECRET_KEY = "fdjkfjdkfj"

    #数据库配置
    SQLALCHEMY_DATABASE_URI = "mysql+pymysql://root:123456@127.0.0.1:3306/information10"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # 配置redis
    REDIS_HOST = "127.0.0.1"
    REDIS_PORT = 6379

    # 配置session信息
    SESSION_TYPE = "redis" #存储类型
    SESSION_USE_SIGNER = True #签名存储
    SESSION_REDIS = redis.StrictRedis(host=REDIS_HOST,port=REDIS_PORT) #指定存储位置
    PERMANENT_SESSION_LIFETIME = 3600*24*2 #设置session两天有效

    #默认日志输出就是debug
    LEVEL = logging.DEBUG

#开发环境
class DevelopConfig(Config):
    pass

#生产环境(线上)
class ProductConfig(Config):
    DEBUG = False
    LEVEL = logging.ERROR
    pass

#测试环境
class TestingConfig(Config):
    TESTING = True

#提供不同环境下的配置启动入口
config_dict = {
    "develop":DevelopConfig,
    "product":ProductConfig,
    "testing":TestingConfig

}