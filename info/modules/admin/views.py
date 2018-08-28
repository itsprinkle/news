import time
from datetime import datetime, timedelta

from flask import render_template, request, current_app, session, redirect, url_for, g, jsonify

from info import user_login_data, constants, db
from info.models import User, News, Category
from info.utils.image_storage import image_storage
from info.utils.response_code import RET
from . import admin_blu

# 功能描述: 退出用户
# 请求路径: /passport/logout
# 请求方式: POST
# 请求参数: 无
# 返回值: errno, errmsg
@admin_blu.route('/logout', methods=['POST'])
def logout():
    #1.清空session信息
    # session.clear()
    session.pop("user_id",None)
    session.pop("nick_name",None)
    session.pop("mobile",None)
    session.pop("is_admin",None)

    #2.返回响应
    return jsonify(errno=RET.OK,errmsg="退出成功")

# 请求路径: /admin/add_category
# 请求方式: POST
# 请求参数: id,name
# 返回值:errno,errmsg
@admin_blu.route('/add_category', methods=['POST'])
def add_category():
    #1.获取参数
    category_id = request.json.get("id")
    category_name = request.json.get("name")

    #2.校验参数
    if not category_name:
        return jsonify(errno=RET.NODATA,errmsg="分类名称不能为空")

    #3.根据是否有分类编号判断, 是修改还是/增加
    if category_id:

        #查询分类对象
        try:
            category = Category.query.get(category_id)
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.DBERR,errmsg="获取分类失败")

        #判断分类对象是否存在
        if not category:
            return jsonify(errno=RET.NODATA, errmsg="分类不存在")

        #修改分类名称
        category.name = category_name

    else:
        #创建分类对象
        category = Category()

        #设置属性
        category.name = category_name

        #保存到数据库
        try:
            db.session.add(category)
            db.session.commit()
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.DBERR,errmsg="新增分类失败")

    #4.返回响应
    return jsonify(errno=RET.OK,errmsg="操作成功")

# 新闻分类数据展示
# 请求路径: /admin/news_category
# 请求方式: GET
# 请求参数: GET,无
# 返回值:GET,渲染news_type.html页面, data数据
@admin_blu.route('/news_category')
def news_category():
    #1.查询所有分类对象
    try:
        categories = Category.query.all()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg="获取分类失败")

    #2.将对象列表转成字典列表
    category_list = []
    for category in categories:
        category_list.append(category.to_dict())

    #3.携带数据渲染页面
    return render_template('admin/news_type.html',categories=category_list)


# 请求路径: /admin/news_edit_detail
# 请求方式: GET, POST
# 请求参数: GET, news_id, POST(news_id,title,digest,content,index_image,category_id)
# 返回值:GET,渲染news_edit_detail.html页面,data字典数据, POST(errno,errmsg)
@admin_blu.route('/news_edit_detail', methods=['GET', 'POST'])
def news_edit_detail():
    """
    1.第一次进入是GEt请求,携带新闻数据渲染页面
    2.第二次进入是POST请求,获取参数
    3.校验参数,为空校验,操作类型校验
    4.通过新闻编号获取新闻对象
    5.判断新闻对象是否存在
    6.根据操作类型,修改新闻状态
    7.返回响应
    :return:
    """
    # 1.第一次进入是GEt请求,携带新闻数据渲染页面
    if request.method == "GET":
        # 1.1获取新闻编号
        news_id = request.args.get("news_id")

        # 1.2获取新闻对象
        try:
            news = News.query.get(news_id)
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.DBERR, errmsg="获取新闻失败")

        # 1.3判断新闻是否存在
        if not news:
            return jsonify(errno=RET.NODATA, errmsg="新闻不存在")

        #1.4 查询分类信息
        try:
            categories = Category.query.all()
            categories.pop(0) #弹出最新
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.DBERR,errmsg="分类获取失败")

        #对象列表转成字典列表
        category_list = []
        for category in categories:
            category_list.append(category.to_dict())


        # 1.5携带新闻数据渲染页面
        return render_template('admin/news_edit_detail.html', news=news.to_dict(),categories=category_list)

    # 2.第二次进入是POST请求,获取参数
    news_id = request.form.get("news_id")
    title = request.form.get("title")
    digest = request.form.get("digest")
    content = request.form.get("content")
    index_image = request.files.get("index_image")
    category_id = request.form.get("category_id")

    # 3.校验参数,为空校验,操作类型校验
    if not all([news_id, title,digest,content,index_image,category_id]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数不全")

    # 4.通过新闻编号获取新闻对象
    try:
        news = News.query.get(news_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="获取新闻失败")

    # 5.判断新闻对象是否存在
    if not news:
        return jsonify(errno=RET.NODATA, errmsg="新闻不存在")

    # 6.上传图片
    try:
        image_name = image_storage(index_image.read())
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.THIRDERR,errmsg="七牛云上传失败")

    #7判断图片是否上传成功
    if not image_name:
        return jsonify(errno=RET.NODATA,errmsg="上传图片失败")

    #8.修改新闻对象数据
    try:
        news.title = title
        news.digest = digest
        news.content = content
        news.index_image_url = constants.QINIU_DOMIN_PREFIX + image_name
        news.category_id = category_id
    except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.DBERR,errmsg="操作失败")

    # 返回响应
    return jsonify(errno=RET.OK, errmsg="操作成功")


# 新闻编辑,详情展示
# 请求路径: /admin/news_edit
# 请求方式: GET
# 请求参数: GET, p, keywords
# 返回值:GET,渲染news_edit.html页面,data字典数据
@admin_blu.route('/news_edit')
def news_edit():
    """
      1.获取参数
      2.参数类型转换
      3.分页查询
      4.获取总页数,当前页,当前页对象
      5.当前页对象列表转成字典列表
      6.携带数据渲染页面
      :return:
      """
    # 1.获取参数
    page = request.args.get("p", 1)
    keywords = request.args.get("keywords")

    # 2.参数类型转换
    try:
        page = int(page)
    except Exception as e:
        current_app.logger.error(e)
        page = 1

    # 3.分页查询
    try:

        #判断是否有搜索关键字
        filters = []
        if keywords:
            filters.append(News.title.contains(keywords))

        paginate = News.query.filter(*filters).order_by(News.create_time.desc()).paginate(page, 10, False)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="获取用户列表失败")

    # 4.获取总页数,当前页,当前页对象
    totalPage = paginate.pages
    currentPage = paginate.page
    items = paginate.items

    # 5.当前页对象列表转成字典列表
    news_list = []
    for item in items:
        news_list.append(item.to_review_dict())

    # 6.携带数据渲染页面
    data = {
        "totalPage": totalPage,
        "currentPage": currentPage,
        "news_list": news_list
    }
    return render_template('admin/news_edit.html', data=data)


# 获取新闻审核,详情
# 请求路径: /admin/news_review_detail
# 请求方式: GET,POST
# 请求参数: GET, news_id, POST,news_id, action
# 返回值:GET,渲染news_review_detail.html页面,data字典数据
@admin_blu.route('/news_review_detail', methods=['GET', 'POST'])
def news_review_detail():
    """
    1.第一次进入是GEt请求,携带新闻数据渲染页面
    2.第二次进入是POST请求,获取参数
    3.校验参数,为空校验,操作类型校验
    4.通过新闻编号获取新闻对象
    5.判断新闻对象是否存在
    6.根据操作类型,修改新闻状态
    7.返回响应
    :return:
    """
    # 1.第一次进入是GEt请求,携带新闻数据渲染页面
    if request.method == "GET":
        #1.1获取新闻编号
        news_id = request.args.get("news_id")

        #1.2获取新闻对象
        try:
            news = News.query.get(news_id)
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.DBERR,errmsg="获取新闻失败")

        #1.3判断新闻是否存在
        if not news:
            return jsonify(errno=RET.NODATA,errmsg="新闻不存在")

        #1.4携带新闻数据渲染页面
        return render_template('admin/news_review_detail.html',news=news.to_dict())

    # 2.第二次进入是POST请求,获取参数
    news_id = request.json.get("news_id")
    action = request.json.get("action")

    # 3.校验参数,为空校验,操作类型校验
    if not all([news_id,action]):
        return jsonify(errno=RET.PARAMERR,errmsg="参数不全")

    if  not action in ["accept","reject"]:
        return jsonify(errno=RET.DATAERR,errmsg="操作类型有误")

    # 4.通过新闻编号获取新闻对象
    try:
        news = News.query.get(news_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="获取新闻失败")

    # 5.判断新闻对象是否存在
    if not news:
        return jsonify(errno=RET.NODATA, errmsg="新闻不存在")
    
    # 6.根据操作类型,修改新闻状态
    try:
        if action == 'accept':
            news.status = 0
        else:
            #获取拒绝原因
            reason = request.json.get("reason")
            #判断
            if not reason: return jsonify(errno=RET.NODATA,errmsg="拒绝原因必须填写")
            news.status = -1
            news.reason = reason
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg="操作失败")
    
    # 7.返回响应
    return jsonify(errno=RET.OK,errmsg="操作成功")


# 获取新闻审核列表
# 请求路径: /admin/news_review
# 请求方式: GET
# 请求参数: GET, p
# 返回值:渲染user_list.html页面,data字典数据
@admin_blu.route('/news_review')
def news_review():
    """
      1.获取参数
      2.参数类型转换
      3.分页查询
      4.获取总页数,当前页,当前页对象
      5.当前页对象列表转成字典列表
      6.携带数据渲染页面
      :return:
      """
    # 1.获取参数
    page = request.args.get("p", 1)
    keywords = request.args.get("keywords")

    # 2.参数类型转换
    try:
        page = int(page)
    except Exception as e:
        current_app.logger.error(e)
        page = 1

    # 3.分页查询
    try:

        #判断是否有搜索关键字
        filters = [News.status != 0]
        if keywords:
            filters.append(News.title.contains(keywords))

        paginate = News.query.filter(*filters).order_by(News.create_time.desc()).paginate(page, 2, False)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="获取用户列表失败")

    # 4.获取总页数,当前页,当前页对象
    totalPage = paginate.pages
    currentPage = paginate.page
    items = paginate.items

    # 5.当前页对象列表转成字典列表
    news_list = []
    for item in items:
        news_list.append(item.to_review_dict())

    # 6.携带数据渲染页面
    data = {
        "totalPage": totalPage,
        "currentPage": currentPage,
        "news_list": news_list
    }
    return render_template('admin/news_review.html', data=data)

# 获取用户列表
# 请求路径: /admin/user_list
# 请求方式: GET
# 请求参数: p
# 返回值:渲染user_list.html页面,data字典数据
@admin_blu.route('/user_list')
def uesr_list():
    """
    1.获取参数
    2.参数类型转换
    3.分页查询
    4.获取总页数,当前页,当前页对象
    5.当前页对象列表转成字典列表
    6.携带数据渲染页面
    :return:
    """
    # 1.获取参数
    page = request.args.get("p",1)

    # 2.参数类型转换
    try:
        page = int(page)
    except Exception as e:
        current_app.logger.error(e)
        page = 1

    # 3.分页查询
    try:
        paginate = User.query.filter(User.is_admin == False).order_by(User.create_time.desc()).paginate(page,10,False)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg="获取用户列表失败")

    # 4.获取总页数,当前页,当前页对象
    totalPage = paginate.pages
    currentPage = paginate.page
    items = paginate.items

    # 5.当前页对象列表转成字典列表
    user_list = []
    for item in items:
        user_list.append(item.to_admin_dict())

    # 6.携带数据渲染页面
    data = {
        "totalPage":totalPage,
        "currentPage":currentPage,
        "user_list":user_list
    }
    return render_template('admin/user_list.html',data=data)


# 统计活跃人数
# 请求路径: /admin/user_count
# 请求方式: GET
# 请求参数: 无
# 返回值:渲染页面user_count.html,字典数据
@admin_blu.route('/user_count')
def user_count():
    """
    思路分析:
    1.查询数据库所有的用户人数
    2.查询本月登陆过的用户人数
    3.查询本日登陆过的用户人数
    4.活跃时间段,活跃人数
    5.拼接数据,渲染页面
    :return:
    """
    # 1.查询数据库所有的用户人数
    try:
        total_count = User.query.filter(User.is_admin == False).count()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg="获取总人数失败")

    # 2.查询本月登陆过的用户人数
    #获取日历对象
    cal = time.localtime()
    try:
        #本月1号0点
        mon_start_str = "%d-%d-01"%(cal.tm_year,cal.tm_mon)
        #转成日期对象
        mon_start_date = datetime.strptime(mon_start_str,"%Y-%m-%d")

        #查询
        mon_count = User.query.filter(User.is_admin == False,User.last_login >= mon_start_date).count()

    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg="获取月活人数失败")


    # 3.查询本日登陆过的用户人数
    try:

        #本日0点
        day_start_str = "%d-%d-%d"%(cal.tm_year,cal.tm_mon,cal.tm_mday)
        #转成日期对象
        day_start_date = datetime.strptime(day_start_str,"%Y-%m-%d")

        #查询
        day_count = User.query.filter(User.is_admin == False,User.last_login >= day_start_date).count()

    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg="获取日活人数失败")

    # 4.活跃时间段,活跃人数
    active_date = []
    active_count = []
    for i in range(0, 31):
        # 当天开始时间A
        begin_date = day_start_date - timedelta(days=i)
        # 当天开始时间, 的后一天B
        end_date = day_start_date - timedelta(days=i - 1)

        # 添加当天开始时间字符串到, 活跃日期中
        active_date.append(begin_date.strftime("%Y-%m-%d"))

        # 查询时间A到B这一天的注册人数
        everyday_active_count = User.query.filter(User.is_admin == False, User.last_login >= begin_date,
                                                  User.last_login <= end_date).count()

        # 添加当天注册人数到,获取数量中
        active_count.append(everyday_active_count)

    #为了方便查看图表,反转
    active_count.reverse()
    active_date.reverse()


    # 5.拼接数据,渲染页面
    data = {
        "total_count":total_count,
        "mon_count":mon_count,
        "day_count":day_count,
        "active_date":active_date,
        "active_count":active_count
    }
    return render_template('admin/user_count.html',data=data)


# 请求路径: /admin/index
# 请求方式: GET
# 请求参数: 无
# 返回值:渲染页面index.html,user字典数据
@admin_blu.route('/index')
@user_login_data
def admin_index():


    data = {
        "admin_info":g.user.to_dict() if g.user else ""
    }
    return render_template('admin/index.html',data=data)



# 请求路径: /admin/login
# 请求方式: GET,POST
# 请求参数:GET,无, POST,username,password
# 返回值: GET渲染login.html页面, POST,login.html页面,errmsg
@admin_blu.route('/login', methods=['GET', 'POST'])
def admin_login():

    #1.如果第一次进来,GET请求,直接渲染页面
    if request.method == "GET":

        #判断是否有登陆过
        if session.get("is_admin"):
            return redirect(url_for('admin.admin_index'))

        return render_template('admin/login.html')

    #2.如果第二次进来,POST,获取参数
    username = request.form.get("username")
    password = request.form.get("password")

    #3.校验参数
    if not all([username,password]):
        return render_template('admin/login.html',errmsg="参数不全")

    #4.通过用户名查询对象
    try:
        admin = User.query.filter(User.mobile == username,User.is_admin == True).first()
    except Exception as e:
        current_app.logger.error(e)
        return render_template("admin/login.html",errmsg="获取管理元失败")

    #5.判断管理员是否存在
    if not admin:
        return render_template('admin/login.html',errmsg="管理员不存在")

    #6.验证密码
    if not admin.check_passowrd(password):
        return render_template('admin/login.html',errmsg="密码不正确")

    #7.记录管理员session信息
    session["user_id"] = admin.id
    session["nick_name"] = admin.nick_name
    session["mobile"] = admin.mobile
    session["is_admin"] = True

    # return redirect("/admin/index")
    return redirect(url_for('admin.admin_index'))