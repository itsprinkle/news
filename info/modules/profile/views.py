from info import constants, db
from info.models import News, Category
from info.utils.commons import user_login_data
from info.utils.image_storage import image_storage
from info.utils.response_code import RET
from . import profile_blu
from flask import render_template, g, redirect, request, jsonify, current_app


# 获取作者个人中心

@profile_blu.route('/other')

def other():
    """
    # 获取参数
    # 校验参数
    # 获取作者对象
    # 判断作者对象是否存在
    # 携带作者信息渲染
    :return:
    """



























# 获取我的新闻列表
# 请求路径: /user/news_list
# 请求方式:GET
# 请求参数:p
# 返回值:GET渲染user_news_list.html页面
@profile_blu.route('/news_list')
@user_login_data
def news_list():
    """
    思路分析:
    1.获取参数
    2.参数类型转换
    3.根据用户信息,查询该用户收藏的新闻
    4.获取分页对象身上属性信息,总页数,当前页,当前页对象列表
    5.将对象列表,转成字典列表
    6.拼接数据,渲染页面
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

    # 3.根据用户信息,查询该用户收藏的新闻
    try:
        paginate = News.query.filter(News.user_id == g.user.id).order_by(News.create_time.desc()).paginate(page,1,False)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg="获取收藏新闻失败")

    # 4.获取分页对象身上属性信息,总页数,当前页,当前页对象列表
    totalPage = paginate.pages
    currentPage = paginate.page
    items = paginate.items

    # 5.将对象列表,转成字典列表
    news_list = []
    for news in items:
        news_list.append(news.to_review_dict())

    # 6.拼接数据,渲染页面
    data = {
        "totalPage":totalPage,
        "currentPage":currentPage,
        "news_list":news_list
    }
    return render_template('news/user_news_list.html',data=data)



# 功能描述: 发布新闻
# 请求路径: /user/news_release
# 请求方式:GET,POST
# 请求参数:GET无, POST ,title, category_id,digest,index_image,content
# 返回值:GET请求,user_news_release.html, data分类列表字段数据, POST,errno,errmsg
@profile_blu.route('/news_release', methods=['GET', 'POST'])
@user_login_data
def news_release():
    """
    思路分析:
    1.第一次进来GET请求,携带数据返回页面
    2.获取参数
    3.校验参数
    4.上传图片
    5.判断是否上传成功
    6.创建新闻对象,设置属性
    7.保存新闻到数据库
    8.返回响应
    :return:
    """
    # 1.第一次进来GET请求,携带数据返回页面
    if request.method == "GET":

        #查询所有分类信息
        try:
            catetories = Category.query.all()
            catetories.pop(0)#弹出最新
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.DBERR,errmsg="获取新闻分类失败")

        #将对象列表转成字典列表
        catetory_list = []
        for catetory in catetories:
            catetory_list.append(catetory.to_dict())

        return render_template('news/user_news_release.html',catetories=catetory_list)

    # 2.获取参数
    title = request.form.get("title")
    category_id = request.form.get("category_id")
    digest = request.form.get("digest")
    index_image = request.files.get("index_image")
    content = request.form.get("content")

    # 3.校验参数
    if not all([title,category_id,digest,index_image,content]):
        return jsonify(errno=RET.PARAMERR,errmsg="参数不全")

    # 4.上传图片
    try:
        image_name = image_storage(index_image.read())
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.THIRDERR,errmsg="七牛云上传失败")

    # 5.判断是否上传成功
    if not image_name:
        return jsonify(errno=RET.NODATA,errmsg="图片上传失败")

    # 6.创建新闻对象,设置属性
    news = News()
    news.title = title
    news.source = "个人发布"
    news.digest = digest
    news.content = content
    news.index_image_url = constants.QINIU_DOMIN_PREFIX + image_name
    news.category_id = category_id
    news.user_id = g.user.id
    news.status = 1 #当前新闻状态 如果为0代表审核通过，1代表审核中，-1代表审核不通过

    # 7.保存新闻到数据库
    try:
        db.session.add(news)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR,errmsg="新闻发布失败")

    # 8.返回响应
    return jsonify(errno=RET.OK,errmsg="发布成功")


# 获取我的收藏新闻
# 请求路径: /user/collection
# 请求方式:GET
# 请求参数:p(页数)
# 返回值: user_collection.html页面
@profile_blu.route('/collection')
@user_login_data
def user_collection():
    """
    思路分析:
    1.获取参数
    2.参数类型转换
    3.根据用户信息,查询该用户收藏的新闻
    4.获取分页对象身上属性信息,总页数,当前页,当前页对象列表
    5.将对象列表,转成字典列表
    6.拼接数据,渲染页面
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

    # 3.根据用户信息,查询该用户收藏的新闻
    try:
        paginate = g.user.collection_news.order_by(News.create_time.desc()).paginate(page,constants.USER_COLLECTION_MAX_NEWS,False)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg="获取收藏新闻失败")

    # 4.获取分页对象身上属性信息,总页数,当前页,当前页对象列表
    totalPage = paginate.pages
    currentPage = paginate.page
    items = paginate.items

    # 5.将对象列表,转成字典列表
    news_list = []
    for news in items:
        news_list.append(news.to_dict())

    # 6.拼接数据,渲染页面
    data = {
        "totalPage":totalPage,
        "currentPage":currentPage,
        "news_list":news_list
    }
    return render_template('news/user_collection.html',data=data)




# 功能说明: 密码修改
# 请求路径: /user/pass_info
# 请求方式:GET,POST
# 请求参数:GET无, POST有参数,old_password, new_password
# 返回值:GET请求: user_pass_info.html页面,data字典数据, POST请求: errno, errmsg
@profile_blu.route('/pass_info', methods=['GET', 'POST'])
@user_login_data
def pass_info():
    """
    思路分析:
    1.第一次进来的时候展示页面,GET请求,渲染即可
    2.第二次进入,POST请求,获取参数
    3.校验参数,为空校验
    4.密码正确性校验
    5.设置新密码到用户对象
    6.返回响应
    :return:
    """
    # 1.第一次进来的时候展示页面,GET请求,渲染即可
    if request.method == 'GET':
        return render_template('news/user_pass_info.html')

    # 2.第二次进入,POST请求,获取参数
    old_password = request.json.get("old_password")
    new_password = request.json.get("new_password")

    # 3.校验参数,为空校验
    if not all([old_password,new_password]):
        return jsonify(errno=RET.PARAMERR,errmsg="参数不全")

    # 4.密码正确性校验
    if not g.user.check_passowrd(old_password):
        return jsonify(errno=RET.DATAERR,errmsg="旧密码不正确")

    # 5.设置新密码到用户对象
    g.user.password = new_password
    
    # 6.返回响应
    return jsonify(errno=RET.OK,errmsg="修改成功")


# 图片上传后台接口编写:
# 请求路径: /user/pic_info
# 请求方式:GET,POST
# 请求参数:无, POST有参数,avatar
# 返回值:GET请求: user_pci_info.html页面,data字典数据, POST请求: errno, errmsg,avatar_url
@profile_blu.route('/pic_info', methods=['GET', 'POST'])
@user_login_data
def user_pic_info():
    """
    思路分析:
    2.如果是第一次进来,是GET请求,携带用户数据,渲染页面
    3.如果是第二次进入,是POST请求,获取参数头像
    4.校验头像
    5.上传头像
    6.判断头像是否有上传成功
    7.设置头像到用户对象
    8.返回响应,携带最新上传图像
    """
    # 2.如果是第一次进来,是GET请求,携带用户数据,渲染页面
    if request.method == "GET":
        return render_template('news/user_pic_info.html',user=g.user.to_dict())

    # 3.如果是第二次进入,是POST请求,获取参数头像
    avatar = request.files.get("avatar")

    # 4.校验头像
    if not avatar:
        return jsonify(errno=RET.NODATA,errmsg="未选择图片")

    # 5.上传头像
    try:
        #读取图片
        image_data = avatar.read()
        #上传图片
        image_name = image_storage(image_data)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.THIRDERR,errmsg="七牛云上传异常")

    # 6.判断头像是否有上传成功
    if not image_name:
        return jsonify(errno=RET.DATAERR,errmsg="上传失败")

    # 7.设置头像到用户对象
    g.user.avatar_url = image_name

    # 8.返回响应,携带最新上传图像
    data = {
        "avatar_url": constants.QINIU_DOMIN_PREFIX +  image_name
    }
    return jsonify(errno=RET.OK,errmsg="上传成功",data=data)




# 功能描述: 展示用户基本信息
# 请求路径: /user/base_info
# 请求方式:GET,POST
# 请求参数:POST请求有参数,nick_name,signature,gender
# 返回值:errno,errmsg
@profile_blu.route('/base_info',methods=["GET","POST"])
@user_login_data
def base_info():
    """
    思路分析:
    1.如果是第一次进入,是GET请求,拼接用户数据,渲染到页面中
    2.如果是第二次进入,是POST请求,获取参数
    3.校验参数,为空校验,性别校验
    4.设置新的信息到用户对象中
    5.返回响应
    :return:
    """
    # 1.如果是第一次进入,是GET请求,拼接用户数据,渲染到页面中
    if request.method == "GET":
        return render_template('news/user_base_info.html',user = g.user.to_dict())

    # 2.如果是第二次进入,是POST请求,获取参数
    nick_name = request.json.get("nick_name")
    signature = request.json.get("signature")
    gender = request.json.get("gender")

    # 3.校验参数,为空校验,性别校验
    if not all([nick_name,signature,gender]):
        return jsonify(errno=RET.PARAMERR,errmsg="参数不全")

    if not gender in ["MAN","WOMAN"]:
        return jsonify(errno=RET.DATAERR,errmsg="性别异常")

    # 4.设置新的信息到用户对象中
    try:
        g.user.signature = signature
        g.user.nick_name = nick_name
        g.user.gender = gender
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg="修改失败")

    # 5.返回响应
    return jsonify(errno=RET.OK,errmsg="修改成功")

#请求路径: /user/info
# 请求方式:GET
# 请求参数:无
# 返回值: user.html页面,用户字典data数据
@profile_blu.route('/info')
@user_login_data
def user_info():

    if not g.user:
        return redirect('/')

    data = {
        "user_info": g.user.to_dict() if g.user else ""
    }
    return render_template('news/user.html',data=data)
