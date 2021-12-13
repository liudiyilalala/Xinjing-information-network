import random
import re
from . import passport_blu
from flask import abort
from flask import request
from flask import current_app
from info.utils.captcha.captcha import captcha
from ... import redis_store, constants
from flask import make_response
from flask import jsonify


# 获取图片验证码
from ...libs.yuntongxun.sms import CCP
from ...utils.response_code import RET


@passport_blu.route('/image_code')
def get_image_code():
    """
    1. 获取当前的图片编码id
    2. 判断返回的图片编码是否有数据
    3. 如果有数据生成图片验证码
    4. 保存当前生成的验证码到redis
    5. 返回图片验证码到页面
    :return:
    """

    # 1. 获取当前的图片编码id
    # args： 获取url ？后的参数
    get_image_id = request.args.get("imageCodeId", None)

    # 2. 判断返回的图片编码是否有数据
    if not get_image_id:
        return abort(403)

    # 3. 如果有数据生成图片验证码
    name, text, image = captcha.generate_captcha()

    # 4. 保存当前生成的验证码到redis  数据库操作要用try
    try:
        redis_store.set("ImageCodeId_" + get_image_id, text, constants.IMAGE_CODE_REDIS_EXPIRES)
    except Exception as e:
        current_app.logging.error(e)
        abort(500)

    # 5. 返回图片验证码到页面
    response = make_response(image)
    response.headers["Content-Type"] = "image/jpg"
    return response


# 获取短信验证码
@passport_blu.route('/sms_code', methods=["POST"])
def send_sms_code():
    """
    发送短信的逻辑
    1. 获取参数。mobile(手机号)， image_code(用户输入的图片验证码内容)， image_code_id(前端发来随机生成的图片验证码编号。在redis中保存的)
    2. 校验参数. 获取的参数是否符合规则，参数是否有值
    3. 判断图片验证码与redis中保存的是否一致
    4. 如果不一致，返回错误
    5. 生成随机的短信验证码
    6. 将验证码发送给用户
    7. 将验证码保存在redis中，设置保存时间
    8. 告知用户验证码发送成功
    :return:
    """
    # 1. 获取参数  返回字典
    return_dict = request.json
    mobile = return_dict.get("mobile")
    image_code = return_dict.get("image_code")
    image_code_id = return_dict.get("image_code_id")

    # 2. 校验参数. 获取的参数是否符合规则，参数是否有值
    # 判断手机号是否符合规则
    if not re.match("^1[35789][0-9]{9}$", mobile):
        return jsonify(errno=RET.DATAERR, errmsg="手机号输入有误")

    # 判断获取的参数是否有值
    if not all([mobile, image_code, image_code_id]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数不全")

    # 3. 判断图片验证码与redis中保存的是否一致
    # 从redis中取出保存的图片验证码  数据库的操作要用try
    try:
        real_redis_date = redis_store.get("ImageCodeId_" + image_code_id)
    except Exception as e:
        current_app.logging.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据库查询失败")

    # 图片验证码在数据库保存的期限是300s
    if not real_redis_date:
        return jsonify(errno=RET.NODATA, errmsg="图片验证码已过期")

    # 图片验证码与用户输入的不一致
    if real_redis_date.lower() != image_code.lower():
        return jsonify(errno=RET.DATAERR, errmsg="验证码输入错误")

    # 判断手机号是否已经注册

    # 5. 生成随机的短信验证码 保证6位长度，不够在前面补0
    sms_code = "%06d" % random.randint(0, 999999)

    # 6. 将验证码发送给用户
    result = CCP().send_template_sms(mobile, [sms_code, constants.SMS_CODE_REDIS_EXPIRES / 60], 1)
    # current_app.logging.debug("短信验证码的内容：%s" % result)
    # 如果发送的验证码！=0，代表发送失败
    if result != 0:
        return jsonify(errno=RET.THIRDERR, errmsg="验证码发送失败，请重试")

    # 7. 将验证码保存在redis中，设置保存时间
    try:
        redis_store.set("sms_code_" + mobile, sms_code, constants.SMS_CODE_REDIS_EXPIRES)
    except Exception as e:
        current_app.logging.error(e)
        jsonify(errno=RET.DBERR, errmsg="短信验证码保存失败")

    # 8. 告知用户验证码发送成功
    return jsonify(errno=RET.OK, errmsg="验证码已发送")



