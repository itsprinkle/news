import logging
from logging.handlers import RotatingFileHandler

from flask import Flask,session
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
import redis
from flask_wtf import CSRFProtect
from flask_wtf.csrf import generate_csrf
from config import config_dict

#创建对象SQLAlchemy
db = SQLAlchemy()

#定义redis变量
redis_store = None

def create_app(config_name):


    app = Flask(__name__)

    #根据传入的配置名, 获取配置类对象
    config = config_dict.get(config_name)

    #调用日志记录方法
    log_file(config.LEVEL)

    # 加载配置信息
    app.config.from_object(config)

    # 创建SQLAlchemy对象,关联app
    db.init_app(app)

    # 创建redis对象
    global redis_store
    redis_store = redis.StrictRedis(host=config.REDIS_HOST, port=config.REDIS_PORT,decode_responses=True)

    # 读取app中的session信息,指定sessino存储位置
    Session(app)

    # 保护app中的路由路径和视图函数
    # CSRFProtect(app)

    #注册首页蓝图到app中
    from info.modules.index import index_blu
    app.register_blueprint(index_blu)

    # 注册passport_blu(认证蓝图)到app中
    from info.modules.passport import passport_blu
    app.register_blueprint(passport_blu)

    # 使用请求钩子拦截app中所有的请求路径，在cookie中设置csrf_token,传给前端
    @app.after_request
    def after_request(resp):
        csrf_token = generate_csrf()
        resp.set_cookie("csrf_token",csrf_token)
        return resp

    return app


#记录日志信息
def log_file(LEVEL):
    # 设置日志的记录等级,等级有大小关系:DEBUG<INFO<WARING<ERROR,
    logging.basicConfig(level=LEVEL)  # 调试debug级,大于等于DEBUG模式的内容输出才会打印
    # 创建日志记录器，指明日志保存的路径、每个日志文件的最大大小、保存的日志文件个数上限
    file_log_handler = RotatingFileHandler("logs/log", maxBytes=1024*1024*100, backupCount=10)
    # 创建日志记录的格式 日志等级 输入日志信息的文件名 行数 日志信息
    formatter = logging.Formatter('%(levelname)s %(filename)s:%(lineno)d %(message)s')
    # 为刚创建的日志记录器设置日志记录格式
    file_log_handler.setFormatter(formatter)
    # 为全局的日志工具对象（flask app使用的）添加日志记录器
    logging.getLogger().addHandler(file_log_handler)