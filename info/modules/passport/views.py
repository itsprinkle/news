import random
from datetime import datetime

from flask import request, jsonify, current_app, make_response, json, session
import re
from info import redis_store, constants, db
from info.libs.yuntongxun.sms import CCP
from info.models import User
from info.utils.captcha.captcha import captcha
from info.utils.response_code import RET
from . import passport_blu

# 功能描述: 退出用户
# 请求路径: /passport/logout
# 请求方式: POST
# 请求参数: 无
# 返回值: errno, errmsg
@passport_blu.route('/logout', methods=['POST'])
def logout():
    #1.清空session信息
    # session.clear()
    session.pop("user_id",None)
    session.pop("nick_name",None)
    session.pop("mobile",None)
    session.pop("is_admin",None)

    #2.返回响应
    return jsonify(errno=RET.OK,errmsg="退出成功")


# 功能描述: 登陆用户
# 请求路径: /passport/login
# 请求方式: POST
# 请求参数: mobile,password
# 返回值: errno, errmsg
@passport_blu.route('/login', methods=['POST'])
def login():
    """
    思路分析:
    1.获取参数
    2.校验参数,为空校验
    3.通过手机号查询数据库,用户对象
    4.判断用户是否存在
    5.判断密码是否正确
    6.记录用户信息到session中
    7.返回响应
    :return:
    """
    # 1.获取参数
    mobile = request.json.get("mobile")
    password = request.json.get("password")

    # 2.校验参数,为空校验
    if not all([mobile,password]):
        return jsonify(errno=RET.PARAMERR,errmsg="参数不全")

    # 3.通过手机号查询数据库,用户对象
    try:
        user = User.query.filter(User.mobile == mobile).first()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg="查询用户失败")

    # 4.判断用户是否存在
    if not user:
        return jsonify(errno=RET.NODATA,errmsg="该用户不存在")

    # 5.判断密码是否正确
    # if user.password_hash != password:
    if not user.check_passowrd(password):
        return jsonify(errno=RET.DATAERR,errmsg="密码错误")

    # 6.记录用户信息到session中
    session["user_id"] = user.id
    session["nick_name"] = user.nick_name
    session["mobile"] = user.mobile

    #记录用户最后一次登陆时间,设置当前系统时间
    user.last_login = datetime.now()

    # try:
    #     db.session.commit()
    # except Exception as e:
    #     current_app.logger.error(e)

    # 7.返回响应
    return jsonify(errno=RET.OK,errmsg="登陆成功")


# 功能描述: 注册用户
# 请求路径: /passport/register
# 请求方式: POST
# 请求参数: mobile, sms_code,password
# 返回值: errno, errmsg
@passport_blu.route('/register', methods=['POST'])
def register():
    """
    思路分析:
    1.获取参数
    2.为空校验,校验手机号格式
    3.根据手机号取出redis短信验证码
    4.判断短信验证码是否过期
    5.删除短信验证码
    6.判断短信验证码的正确性
    7.创建用户对象,并设置属性
    8.保存用户对象到数据库
    9.返回响应
    :return:
    """
    # 1.获取参数
    # json_data = request.data
    # dict_data = json.loads(json_data)
    #上面两句话等于下面一句话,request.get_json() 或者 request.json
    dict_data = request.json
    mobile = dict_data.get("mobile")
    sms_code = dict_data.get("sms_code")
    password = dict_data.get("password")
    
    # 2.为空校验,校验手机号格式
    if not all([mobile,sms_code,password]):
        return jsonify(errno=RET.PARAMERR,errmsg="参数不全")
    
    if not re.match("1[35789]\d{9}",mobile):
        return jsonify(errno=RET.DATAERR,errmsg="手机格式不正确")
    
    # 3.根据手机号取出redis短信验证码
    try:
        redis_sms_code = redis_store.get("sms_code:%s"%mobile)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg="获取短信验证码失败")
    
    # 4.判断短信验证码是否过期
    if not redis_sms_code:
        return jsonify(errno=RET.NODATA,errmsg="短信验证码已过期")
    
    # 5.删除短信验证码
    try:
        redis_store.delete("sms_code:%s"%mobile)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg="删除短信验证码异常")
    
    # 6.判断短信验证码的正确性
    if sms_code != redis_sms_code:
        return jsonify(errno=RET.DATAERR,errmsg="短信验证码错误")
    
    # 7.创建用户对象,并设置属性
    user = User()
    user.nick_name = mobile
    user.mobile = mobile
    # user.password_hash = password
    user.password = password #加密处理

    # 8.保存用户对象到数据库
    try:
        db.session.add(user)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR,errmsg="用户注册失败")

    # 8.1.记录用户信息到session中
    session["user_id"] = user.id
    session["nick_name"] = user.nick_name
    session["mobile"] = user.mobile

    # 9.返回响应
    return jsonify(errno=RET.OK,errmsg="注册成功")


# 功能描述: 获取短信验证码
# 请求路径: /passport/sms_code
# 请求方式: POST
# 请求参数: mobile, image_code,image_code_id
# 返回值: errno, errmsg
@passport_blu.route('/sms_code', methods=['POST'])
def sms_code():
    """
    分析思路:
    1.获取请求参数
    2.为空校验
    3.校验手机号格式
    4.根据传入的编号,取出redis图片验证码
    5.判断图片验证码是否过期
    6.删除图片验证
    7.判断图片验证码正确性
    8.生成短信验证码,6位随机数
    9.发送短信
    10.判断是否发送成功
    11.保存短信验证码到redis
    12.返回响应
    :return:
    """
    # 1.获取请求参数
    json_data = request.data
    dict_data = json.loads(json_data)
    mobile = dict_data.get("mobile")
    image_code = dict_data.get("image_code")
    image_code_id = dict_data.get("image_code_id")

    # 2.为空校验
    if not all([mobile,image_code,image_code_id]):
        return jsonify(errno=RET.PARAMERR,errmsg="参数不全")

    # 3.校验手机号格式
    if not re.match("1[35789]\d{9}",mobile):
        return jsonify(errno=RET.DATAERR,errmsg="手机格式不正确")

    # 4.根据传入的编号,取出redis图片验证码
    try:
        redis_image_code = redis_store.get("image_code:%s"%image_code_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg="获取图片验证码失败")

    # 5.判断图片验证码是否过期
    if not redis_image_code:
        return jsonify(errno=RET.NODATA,errmsg="图片验证码已过期")

    # 6.删除图片验证
    try:
        redis_store.delete("image_code:%s"%image_code_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg="删除图片验证码失败")

    # 7.判断图片验证码正确性
    if image_code.upper() != redis_image_code.upper():
        return jsonify(errno=RET.DATAERR,errmsg="图片验证码填写错误")

    # 8.生成短信验证码,6位随机数
    sms_code = "%06d"%random.randint(0,999999)
    current_app.logger.debug("短信验证码是 = %s"%sms_code)
    # 9.发送短信
    # try:
    #     ccp = CCP()
    #     result = ccp.send_template_sms(mobile,[sms_code,constants.SMS_CODE_REDIS_EXPIRES/60],1)
    # except Exception as e:
    #     current_app.logger.error(e)
    #     return jsonify(errno=RET.THIRDERR,errmsg="云通讯异常")
    #
    # # 10.判断是否发送成功
    # if result == -1:
    #     return jsonify(errno=RET.DATAERR,errmsg="短信发送失败")

    # 11.保存短信验证码到redis
    try:
        redis_store.set("sms_code:%s"%mobile,sms_code,constants.SMS_CODE_REDIS_EXPIRES)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg="短信验证码保存失败")

    # 12.返回响应
    return jsonify(errno=RET.OK,errmsg="短信发送成功")


#功能描述: 获取图片验证码
# 请求路径: /passport/image_code
# 请求方式: GET
# 请求参数: cur_id, pre_id
# 返回值: 图片验证码
@passport_blu.route('/image_code')
def image_code():
    """
    思路分析:
    1.获取请求参数
    2.校验参数
    3.生成图片验证码
    4.保存图片验证码
    5.判断是否有上个图片验证码编号,如果存在则删除
    6.返回图片验证码
    :return:
    """
    # 1.获取请求参数
    cur_id = request.args.get("cur_id")
    pre_id = request.args.get("pre_id")

    # 2.校验参数
    if not cur_id:
        return jsonify(errno=RET.PARAMERR,errmsg="参数不完整")

    # 3.生成图片验证码
    name,text,image_data = captcha.generate_captcha()

    # 4.保存图片验证码
    try:
        redis_store.set("image_code:%s"%cur_id,text,constants.IMAGE_CODE_REDIS_EXPIRES)

        # 5.判断是否有上个图片验证码编号,如果存在则删除
        if pre_id:
            redis_store.delete("image_code:%s"%pre_id)
    except Exception as e:
        current_app.logger.debug(e)
        return jsonify(errno=RET.DBERR,errmsg="图片验证码操作失败")

    # 6.返回图片验证码
    response = make_response(image_data)
    response.headers["Content-Type"] = "image/jpg"
    return response