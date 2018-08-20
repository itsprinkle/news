from flask import request, jsonify

from info import redis_store, constants
from info.utils.captcha.captcha import captcha
from info.utils.response_code import RET
from . import passport_blu


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
    redis_store.set("image_code:%s"%cur_id,text,constants.IMAGE_CODE_REDIS_EXPIRES)

    # 5.判断是否有上个图片验证码编号,如果存在则删除
    if pre_id:
        redis_store.delete("image_code:%s"%pre_id)

    # 6.返回图片验证码
    return image_data