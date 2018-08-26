from flask import Blueprint

#创建蓝图对象
passport_blu = Blueprint("passport",__name__,url_prefix='/passport')

#装饰视图函数
from . import views