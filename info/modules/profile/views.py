from . import profile_blu
from flask import render_template


#请求路径: /user/info
# 请求方式:GET
# 请求参数:无
# 返回值: user.html页面,用户字典data数据
@profile_blu.route('/info')
def user_info():
    data={

    }
    return render_template('news/user.html',data=data)
