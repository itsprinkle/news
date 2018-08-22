# from info.modules.index import index_blu
from info import redis_store, constants
from info.models import User, News, Category
from info.utils.commons import user_login_data
from info.utils.response_code import RET
from . import index_blu
from flask import render_template, current_app, session, jsonify, request, g


# 功能描述:获取首页新闻列表
# 请求路径: /newslist
# 请求方式: GET
# 请求参数: cid,page,per_page
# 返回值: data数据
@index_blu.route('/newslist')
def news_list():
    """
    思路分析:
    1.获取参数
    2.校验参数(参数类型转化)
    3.分页查询(paginate)
    4.获取分页对象属性,总页数,当前页,当前页对象列表
    5.对象列表,转成字典列表
    6.拼接数据,返回响应
    :return:
    """
    # 1.获取参数
    cid = request.args.get("cid","1")
    page = request.args.get("page",1)
    per_page = request.args.get("per_page",10)

    # 2.校验参数(参数类型转化)
    try:
        page = int(page)
        per_page = int(per_page)
    except Exception as e:
        current_app.logger.error(e)
        page = 1
        per_page = 10

    # 3.分页查询(paginate)
    try:

        #判断分类编号是否等于1
        filters = []
        if cid != '1':
            filters.append(News.category_id == 1)

        paginate = News.query.filter(*filters).order_by(News.create_time.desc()).paginate(page,per_page,False)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg="获取新闻列表失败")

    # 4.获取分页对象属性,总页数,当前页,当前页对象列表
    totalPage = paginate.pages
    currentPage = paginate.page
    items = paginate.items

    # 5.对象列表,转成字典列表
    newsList = []
    for item in items:
        newsList.append(item.to_dict())

    # 6.拼接数据,返回响应
    return jsonify(errno=RET.OK,errmsg="获取新闻列表成功",totalPage=totalPage,currentPage=currentPage,newsList=newsList)


@index_blu.route('/',methods=["POST","GET"])
@user_login_data
def show_index_page():

    #获取session用户编号
    # user_id = session.get("user_id")
    #
    # #查询数据库
    # user = None
    # if user_id:
    #     try:
    #         user = User.query.get(user_id)
    #     except Exception as e:
    #         current_app.logger.error(e)

    #查询热门新闻,取前10条
    try:
        news = News.query.order_by(News.clicks.desc()).limit(constants.CLICK_RANK_MAX_NEWS)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg="热门新闻查询失败")

    #将新闻对象列表,转成字典列表
    click_news_list = []
    for new in news:
        click_news_list.append(new.to_dict())

    #获取分类信息
    try:
        categories = Category.query.all()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg="获取分类失败")

    #将分类对象列表,转成字典列表
    category_list = []
    for category in categories:
        category_list.append(category.to_dict())

    #携带用户数据,渲染到首页页面
    data = {
        # 如果user不为空,返回左边内容,否则返回右边
        "user_info": g.user.to_dict() if g.user else "",
        "click_news_list":click_news_list,
        "category_list":category_list
    }
    return render_template('news/index.html',data=data)

#每个浏览器去访问服务器的时候会自动发送一个GET请求,地址是:/favicon.ico
#flask中提供了一个方法send_static_file(文件A),自动寻找static目录底下的文件A
@index_blu.route('/favicon.ico')
def get_web_logo():

    return current_app.send_static_file('news/favicon.ico')