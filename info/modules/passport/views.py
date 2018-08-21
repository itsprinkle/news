import random
import re

from flask import current_app, jsonify
import json
from flask import make_response
from flask import request
from flask import session

from info import constants, db

from info import redis_store
from info.libs.yuntongxun.sms import CCP
from info.models import User
from info.utils.captcha.captcha import captcha
from info.utils.response_code import RET
from . import passport_blu

# 获取图片验证码
@passport_blu.route('/image_code')
def get_passport():
    #获取图片编号,上一次的编号
    code_id = request.args.get('cur_id')
    pre_id = request.args.get('pre_id')
    # 完整性
    if not all([code_id,pre_id]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数不全")
    # 后台生成图片验证码
    name,text,image = captcha.generate_captcha()
    # 保存验证码(编号+有效期+验证码文本)
    try:
        redis_store.set('image_code:%s'%code_id,text,constants.IMAGE_CODE_REDIS_EXPIRES)
        if pre_id:
            redis_store.delete("image_code:%s"%pre_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.NODATA,errmsg="保存图片验证码失败")

    # 返回响应
    resp = make_response(image)
    resp.headers['Content-Type'] = 'img/jpg'
    return resp


# 获取短信验证码
@passport_blu.route('/sms_code',methods=['POST'])
def send_sms():
    """
    1. 接收参数并判断是否有值
    2. 校验手机号是正确
    3. 通过传入的图片编码去redis中查询真实的图片验证码内容
    4. 进行验证码内容的比对
    5. 生成发送短信的内容并发送短信
    6. redis中保存短信验证码内容
    7. 返回发送成功的响应
    :return:
    """
    # 接收参数
    # json_data = request.data
    # dict_data = json.loads(json_data)
    dict_data = request.json
    mobile = dict_data.get("mobile")
    image_code = dict_data.get("image_code")
    image_code_id = dict_data.get("image_code_id")

    # 完整性
    if not all([mobile,image_code,image_code_id]):
        return jsonify(errno=RET.PARAMERR,errmsg="参数不全")

    # 手机号格式
    if not re.match("1[35789]\d{9}",mobile):
        return jsonify(errno=RET.DATAERR,errmsg="手机格式不正确")

    # 根据传入的编号,取出redis图片验证码
    try:
        redis_image_code = redis_store.get("image_code:%s"%image_code_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg="获取图片验证码失败")

    # 判断图片验证码是否过期
    if not redis_image_code:
        return jsonify(errno=RET.NODATA,errmsg="图片验证码已过期")

    # 删除图片验证
    try:
        redis_store.delete("image_code:%s"%image_code_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg="删除图片验证码失败")

    # 判断图片验证码正确性，大小写
    if image_code.upper() != redis_image_code.upper():
        return jsonify(errno=RET.DATAERR,errmsg="图片验证码填写错误")

    # 生成短信验证码内容,6位随机数
    sms_code = "%06d"%random.randint(0,999999)
    current_app.logger.debug("短信验证码是 = %s"%sms_code)
    # # 发送短信（配置四点：1.主账号 2.auth token 3. app id 4.添加测试号码）
    # try:
    #     ccp = CCP()
    #     result = ccp.send_template_sms(mobile,[sms_code,constants.SMS_CODE_REDIS_EXPIRES/60],1)
    # except Exception as e:
    #     current_app.logger.error(e)
    #     return jsonify(errno=RET.THIRDERR,errmsg="云通讯异常")
    # # 判断是否发送成功
    # if result == -1:
    #     return jsonify(errno=RET.DATAERR,errmsg="短信发送失败")

    # 保存短信验证码到redis
    try:
        redis_store.set("sms_code:%s"%mobile,sms_code,constants.SMS_CODE_REDIS_EXPIRES)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg="短信验证码保存失败")

    # 返回成功响应
    return jsonify(errno=RET.OK,errmsg="短信发送成功")


@passport_blu.route('/register',methods=['POST'])
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
    # 接收参数
    param_dict = request.json
    mobile = param_dict.get("mobile")
    sms_code = param_dict.get("sms_code")
    password = param_dict.get("password")
    # 完整性
    if not all([mobile,sms_code,password]):
        return jsonify(errno = RET.PARAMERR,errmsg = "参数不完整")
    #手机号格式
    if not re.match("^1[345678]\d{9}$",mobile):
        return jsonify(errno = RET.DATAERR,errmsg = "手机号格式错误")
    # 获取sms_code
    try:
        # 注 存取一致（接收验证码时存储时键设为什么，取出来时用什么键）
        msg_code = redis_store.get("sms_code:%s"%mobile)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg = "获取短信验证码失败")
    # 过期验证
    if not msg_code:
        return jsonify(errno=RET.NODATA,errmsg = "短信验证码已过期")
    # 删除msg_code
    try:
        redis_store.delete("sms_code:%s"%mobile)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg = "删除短信验证码失败")

    # 正确性判断
    if sms_code != msg_code:
        return  jsonify(errno = RET.DATAERR,errmsg = "验证码错误")

    # 创建用户对象 设置属性
    user = User()
    user.nick_name = mobile
    user.password_hash = password
    user.mobile = mobile

    # 保存用户对象到数据库
    try:
        db.session.add(user)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR,errmsg = "保存用户失败")

    # 实现注册完成后直接登录显示
    # 记录信息到session中
    session['user_id'] = user.id
    session['nick_name'] = user.nick_name
    session['mobile'] = user.mobile

    return jsonify(errno=RET.OK,errmsg = "注册成功")


@passport_blu.route('/login',methods = ['POST'])
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
    # 接收参数mobile password
    # param_dict = request.json
    # mobile = param_dict.get("mobile")
    # password = param_dict.get("password")

    mobile = request.json.get("mobile")
    password = request.json.get("password")
    # 完整性
    if not all([mobile,password]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数不完整")
    # 查询手机号
    try:
        user = User.query.filter(User.mobile == mobile).first()
        print(user)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="用户查询失败")
    # 判断用户是否存在
    if not user:
        return jsonify(errno=RET.DBERR, errmsg="用户不存在")

    # 校验密码
    if password != user.password_hash:
        return jsonify(errno=RET.DATAERR, errmsg="密码错误")

    # 记录信息到session中
    session['user_id'] = user.id
    session['nick_name'] = user.nick_name
    session['mobile'] = user.mobile

    # 返回成功信息
    return jsonify(errno = RET.OK,errmsg='登录成功')


# 退出功能实现
# @passport_blu.route('/logout',methods=['POST'])
# def logout():
#     """
#     # 删除之前保存到服务器的session
#     :return:
#     """
#     session.pop('user.id',None)
#     session.pop('user.nick_name', None)
#     session.pop('user.mobile', None)
#     return jsonify(errno=RET.OK,errmsg="ok")




