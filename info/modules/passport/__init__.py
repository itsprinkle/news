# 创建蓝图

from flask import Blueprint
# 创建对象
# prefix 设置蓝图前缀
passport_blu = Blueprint("passport",__name__,url_prefix="/passport")

# 装饰视图函数
from . import views




