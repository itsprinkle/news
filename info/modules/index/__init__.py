from flask import Blueprint

#创建首页蓝图
index_blu = Blueprint("index",__name__)

#装饰视图函数
from . import views
