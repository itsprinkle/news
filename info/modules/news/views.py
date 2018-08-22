from info.models import User, News
from info.utils.commons import user_login_data
from info.utils.response_code import RET
from . import news_blu
from flask import render_template, session, current_app, g, jsonify


#功能描述: 新闻详情
# 请求路径: /news/<int:news_id>
# 请求方式: GET
# 请求参数:news_id
# 返回值: detail.html页面, 用户data字典数据
@news_blu.route('/<int:news_id>')
@user_login_data
def news_detail(news_id):

    # #获取用户编号
    # user_id = session.get("user_id")
    #
    # #查询用户对象
    # user = None
    # if user_id:
    #     try:
    #         user = User.query.get(user_id)
    #     except Exception as e:
    #         current_app.logger.error(e)

    #查询热门新闻
    try:
        news = News.query.order_by(News.clicks.desc()).limit(8)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg="获取热门新闻失败")

    #将新闻对象列表,转成字典列表
    click_news_list = []
    for news in news:
        click_news_list.append(news.to_dict())

    #拼接数据渲染页面
    data = {
        "user_info": g.user.to_dict() if g.user else "",
        "click_news_list":click_news_list
    }
    return render_template('news/detail.html',data=data)
