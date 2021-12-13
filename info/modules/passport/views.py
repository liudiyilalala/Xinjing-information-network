from . import passport_blu
from flask import abort
from flask import request
from flask import current_app
from info.utils.captcha.captcha import captcha
from ... import redis_store, constants
from flask import make_response


# 获取图片验证码
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

