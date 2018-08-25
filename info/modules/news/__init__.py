from flask import Blueprint

#创建新闻蓝图
news_blu = Blueprint("news",__name__,url_prefix='/news')

#装饰视图函数
from . import views