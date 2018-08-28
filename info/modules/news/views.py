from info import db
from info.models import User, News, Comment, CommentLike
from info.utils.commons import user_login_data
from info.utils.response_code import RET
from . import news_blu
from flask import render_template, session, current_app, g, jsonify, abort, request




# 关注/取消关注作者
# 请求路径: /news/followed_user
# 请求方式: POST
# 请求参数:user_id,action
# 返回值: errno, errmsg
@news_blu.route('/followed_user', methods=['POST'])
@user_login_data
def followed_user():
    """
    1.判断用户是否登陆
    2.获取参数
    3.校验参数,为空校验,操作类型校验
    4.获取作者对象
    5.判断作者对象是否存在
    6.根据操作类型,取消/关注
    7.返回响应
    :return:
    """
    # 1.判断用户是否登陆
    if not g.user:
        return jsonify(errno=RET.PARAMERR,errmsg="用户未登录")

    # 2.获取参数
    author_id = request.json.get("user_id")
    action = request.json.get("action")

    # 3.校验参数,为空校验,操作类型校验
    if not all([author_id,action]):
        return jsonify(errno=RET.PARAMERR,errmsg="参数不全")

    if not action in ["follow","unfollow"]:
        return jsonify(errno=RET.DATAERR,errmsg="操作类型有误")

    # 4.获取作者对象
    try:
        author = User.query.get(author_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg="作者获取失败")
    
    # 5.判断作者对象是否存在
    if not author:
        return jsonify(errno=RET.NODATA,errmsg="该作者不存在")
    
    # 6.根据操作类型,取消/关注
    try:
        if action == "follow":
            #判断是否有关注过
            if not g.user in author.followers:
                author.followers.append(g.user)
        else:
            #判断是否有关注过
            if  g.user in author.followers:
                author.followers.remove(g.user)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg="操作失败")
        
    # 7.返回响应
    return jsonify(errno=RET.OK,errmsg="操作成功")


# 功能描述: 点赞/取消点赞
# 请求路径: /news/comment_like
# 请求方式: POST
# 请求参数:comment_id,action,g.user
# 返回值: errno,errmsg
@news_blu.route('/comment_like',methods=["POST"])
@user_login_data
def comment_like():
    """
    思路分析:
    1.判断用户是否有登陆
    2.获取参数
    3.校验参数,为空校验,操作类型
    4.根据评论编号取出评论对象
    5.判断评论对象是否存在
    6.根据操作类型,点赞/取消点赞
    7.返回响应
    :return:
    """
    # 1.判断用户是否有登陆
    if not g.user:
        return jsonify(errno=RET.NODATA,errmsg="用户未登录")

    # 2.获取参数
    comment_id = request.json.get("comment_id")
    action = request.json.get("action")

    # 3.校验参数,为空校验,操作类型
    if not all([comment_id,action]):
        return jsonify(errno=RET.PARAMERR,errmsg="参数不全")

    if not action in ["add","remove"]:
        return jsonify(errno=RET.DATAERR,errmsg="操作类型有误")

    # 4.根据评论编号取出评论对象
    try:
        comment = Comment.query.get(comment_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg="查询评论失败")

    # 5.判断评论对象是否存在
    if not comment: return jsonify(errno=RET.NODATA,errmsg="评论不存在")

    # 6.根据操作类型,点赞/取消点赞
    try:
        if action == "add":
            #判断用户是否点过赞了
            comment_like = CommentLike.query.filter(CommentLike.comment_id == comment_id,CommentLike.user_id == g.user.id).first()
            if not comment_like:
                #创建点赞对象
                comment_like = CommentLike()

                #设置属性
                comment_like.comment_id = comment_id
                comment_like.user_id = g.user.id

                #保存点赞对象到数据库
                db.session.add(comment_like)
                db.session.commit()

                #将该评论的点赞数量+1
                comment.like_count += 1

        else:
            # 判断用户是否点过赞了
            comment_like = CommentLike.query.filter(CommentLike.comment_id == comment_id,
                                                    CommentLike.user_id == g.user.id).first()
            if  comment_like:
                # 取消点赞对象到数据库
                db.session.delete(comment_like)
                db.session.commit()

                # 将该评论的点赞数量-1
                if comment.like_count > 0:
                    comment.like_count -= 1
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg="操作失败")

    # 7.返回响应
    return jsonify(errno=RET.OK,errmsg="操作成功")



# 功能描述: 评论/回复评论
# 请求路径: /news/news_comment
# 请求方式: POST
# 请求参数:news_id,comment,parent_id, g.user
# 返回值: errno,errmsg,评论字典
@news_blu.route('/news_comment', methods=['POST'])
@user_login_data
def news_comment():
    """
    思路分析:
    1.判断用户是否有登陆
    2.获取参数
    3.校验参数
    4.根据新闻编号获取新闻对象
    5.判断新闻是否存在
    6.创建评论对象
    7.设置评论对象属性
    8.保存到数据库
    9.返回响应
    :return:
    """
    # 1.判断用户是否有登陆
    if not g.user:
        return jsonify(errno=RET.NODATA,errmsg="用户未登录")

    # 2.获取参数
    news_id = request.json.get("news_id")
    content = request.json.get("comment")
    parent_id = request.json.get("parent_id")

    # 3.校验参数
    if not all([news_id,content]):
        return jsonify(errno=RET.PARAMERR,errmsg="参数不全")

    # 4.根据新闻编号获取新闻对象
    try:
        news = News.query.get(news_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg="新闻查询失败")

    # 5.判断新闻是否存在
    if not news:
        return jsonify(errno=RET.NODATA,errmsg="新闻不能存在")

    # 6.创建评论对象
    comment = Comment()

    # 7.设置评论对象属性
    comment.user_id = g.user.id
    comment.news_id = news_id
    comment.content = content

    #判断是否父评论
    if parent_id:
        comment.parent_id = parent_id

    # 8.保存到数据库
    try:
        db.session.add(comment)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg="评论失败")

    # 9.返回响应
    return jsonify(errno=RET.OK,errmsg="评论成功",data=comment.to_dict())


# 功能描述: 收藏/取消收藏
# 请求路径: /news/news_collect
# 请求方式: POST
# 请求参数:news_id,action, g.user
# 返回值: errno,errmsg
@news_blu.route('/news_collect', methods=['POST'])
@user_login_data
def news_collect():
    """
    思路分析:
    1.判断用户是否有登陆
    2.获取参数
    3.校验参数,为空校验,操作类型校验
    4.通过新闻编号,取出新闻对象
    5.判断新闻是否存在
    6.根据操作类型,收藏/取消收藏
    7.返回响应
    :return:
    """
    # 1.判断用户是否有登陆
    if not g.user:
        return jsonify(errno=RET.NODATA,errmsg="未登录")

    # 2.获取参数
    news_id = request.json.get("news_id")
    action = request.json.get("action")

    # 3.校验参数,为空校验,操作类型校验
    if not all([news_id,action]):
        return jsonify(errno=RET.PARAMERR,errmsg="参数不全")

    if not action in ['collect','cancel_collect']:
        return jsonify(errno=RET.DATAERR,errmsg="操作类型有误")

    # 4.通过新闻编号,取出新闻对象
    try:
        news = News.query.get(news_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg="新闻查询失败")

    # 5.判断新闻是否存在
    if not news:
        return jsonify(errno=RET.NODATA,errmsg="新闻不存在")

    # 6.根据操作类型,收藏/取消收藏
    try:
        if action == "collect":
            #判断是否收藏过该新闻
            if not news in g.user.collection_news:
                g.user.collection_news.append(news)
        else:
            #判断是否收藏过该新闻
            if  news in g.user.collection_news:
                g.user.collection_news.remove(news)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg="操作失败")

    # 7.返回响应
    return jsonify(errno=RET.OK,errmsg="操作成功")



#功能描述: 新闻详情
# 请求路径: /news/<int:news_id>
# 请求方式: GET
# 请求参数:news_id
# 返回值: detail.html页面, 用户data字典数据
@news_blu.route('/<int:news_id>')
@user_login_data
def news_detail(news_id):

    #通过新闻编号,查询新闻对象
    try:
        detail_news = News.query.get(news_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg="新闻查询失败")

    #判断新闻是否存在, 后续对404做统一处理
    if not detail_news:
        abort(404)


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

    #判断用户是否有收藏过该新闻
    is_collected = False
    if g.user and detail_news in g.user.collection_news:
        is_collected = True

    #查询所有的评论信息
    try:
        comments = Comment.query.filter(Comment.news_id == news_id).order_by(Comment.create_time.desc()).all()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg="查询评论失败")

    #判断用户是否有登陆
    comment_ids = [] #记录用户点赞过的,评论编号
    if g.user:
        # 用户所有的点赞
        comment_likes = g.user.comment_likes

        # 通过点赞对象,评论编号
        for comment_like in comment_likes:
            comment_ids.append(comment_like.comment_id)

    #将评论列表转成字典列表
    comment_list = []
    for comment in comments:
        comment_dict = comment.to_dict()
        #设置用户对当前评论的点赞状态
        comment_dict["is_like"] = False
        #判断用户,是否点过赞
        # if 用户登陆 and  评论的编号,在用户所有点赞的评论编号里面:
        if g.user and  comment.id in comment_ids:
            comment_dict["is_like"] = True

        comment_list.append(comment_dict)

    #判断当前用户是否有关注,该新闻的作者
    is_followed = False
    if g.user and news.user:
        if g.user in news.user.followers:
            is_followed = True

    #拼接数据渲染页面
    data = {
        "user_info": g.user.to_dict() if g.user else "",
        "click_news_list":click_news_list,
        "news":detail_news.to_dict(),
        "is_collected":is_collected,
        "comments":comment_list,
        "is_followed":is_followed
    }
    return render_template('news/detail.html',data=data)
