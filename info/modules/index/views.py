# from info.modules.index import index_blu
from info import redis_store
from info.models import User
from . import index_blu
from flask import render_template, current_app, session


@index_blu.route('/',methods=["POST","GET"])
def show_index_page():

    #获取session用户编号
    user_id = session.get("user_id")

    #查询数据库
    user = None
    if user_id:
        try:
            user = User.query.get(user_id)
        except Exception as e:
            current_app.logger.error(e)

    #携带用户数据,渲染到首页页面
    data = {
        # 如果user不为空,返回左边内容,否则返回右边
        "user_info": user.to_dict() if user else ""
    }
    return render_template('news/index.html',data=data)

#每个浏览器去访问服务器的时候会自动发送一个GET请求,地址是:/favicon.ico
#flask中提供了一个方法send_static_file(文件A),自动寻找static目录底下的文件A
@index_blu.route('/favicon.ico')
def get_web_logo():

    return current_app.send_static_file('news/favicon.ico')