from qiniu import Auth, put_data
from flask import current_app

# 需要填写你的 Access Key 和 Secret Key
access_key = 'YVOI41r_wKXKv501HyLgOF1QjJp4ZviweQGFIm-K'
secret_key = 'pxiDF2Yil359UpoLUcVyvi4C64ezfa7-Vl2kv0vy'

# 要上传的空间
bucket_name = 'ldyhome'


def storage(data):
    """七牛云存储上传文件接口"""
    if not data:
        return None
    try:
        # 构建鉴权对象
        q = Auth(access_key, secret_key)

        # 生成上传 Token，可以指定过期时间等
        token = q.upload_token(bucket_name)

        # 上传文件
        ret, info = put_data(token, None, data)

    except Exception as e:
        current_app.logger.error(e)
        raise e

    if info and info.status_code != 200:
        raise Exception("上传文件到七牛失败")

    # 返回七牛中保存的图片名，这个图片名也是访问七牛获取图片的路径
    return ret["key"]


if __name__ == '__main__':
    file_name = input("输入上传的文件")
    with open(file_name, "rb") as f:
        storage(f.read())
