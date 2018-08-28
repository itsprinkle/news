from flask import Blueprint, request, session, redirect

#创建管理员蓝图
admin_blu = Blueprint("admin",__name__,url_prefix="/admin")

#装饰视图函数
from . import views


#编写请求钩子方法,只要访问了管理员的任何页面都做拦截
@admin_blu.before_request
def before_request():
    # print("访问地址是 = %s"%request.url)

    #判断访问的是否是登录页面
    # if request.url.endswith('/admin/login'):
    #     pass
    # else:
    #     #判断是不是管理员
    #     if session.get("is_admin"):
    #         pass
    #     else:
    #         return redirect('/')

    #优化
    if not request.url.endswith('/admin/login'):
        if not session.get("is_admin"):
            return redirect('/')