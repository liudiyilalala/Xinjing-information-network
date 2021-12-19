from info import constants, db
from info.models import Category, News
from info.modules.profile import profile_blu
from flask import render_template
from flask import g
from info.utils.common import user_login_data
from flask import redirect
from flask import request
from flask import jsonify

from info.utils.image_storage import storage
from info.utils.response_code import RET
from flask import current_app


@profile_blu.route('/info')
@user_login_data
def user_info():
    user = g.user
    if not user:
        return redirect("/")
    data = {
        "user": user.to_dict() if user else None
    }
    return render_template("news/user.html", data=data)


# 基本资料展示
@profile_blu.route("/base_info", methods=["GET", "POST"])
@user_login_data
def base_info():
    # 不同的请求做不同的时期 get请求返回html页面
    if request.method == "GET":
        return render_template("news/user_base_info.html", data={"user": g.user.to_dict()})

    # post请求进行基本资料的修改
    # 1. 获取参数 nick_name(昵称)  signature(个性签名) gender(性别 MAN/WOMAN)
    nick_name = request.json.get("nick_name")
    signature = request.json.get("signature")
    gender = request.json.get("gender")

    # 2. 校验参数
    if not all([nick_name, signature, gender]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    if gender not in (["MAN", "WOMAN"]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    # 3. 修改该用户数据库内的信息
    user = g.user
    user.nick_name = nick_name
    user.signature = signature
    user.gender = gender

    return jsonify(errno=RET.OK, errmsg="OK")


# 头像上传逻辑实现
@profile_blu.route("/pic_info", methods=["GET", "POST"])
@user_login_data
def pic_info():
    user = g.user
    # 不同的请求做不同的时期 get请求返回html页面
    if request.method == "GET":
        return render_template("news/user_pic_info.html", data={"user": user.to_dict()})

    # post请求进行头像的上传
    # 1. 获取参数 avatar(头像) 将获取到的头像读取
    try:
        avatar_pic = request.files.get("avatar").read()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg="获取图片失败")

    # 2. 将文件上传到七牛云
    try:
        avatar_pic_url = storage(avatar_pic)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.THIRDERR, errmsg="图片上传失败")

    # 3. 将头像路径保存到数据库,并将图片url返回给前端
    user.avatar_url = avatar_pic_url

    return jsonify(errno=RET.OK, errmsg="OK", data={"avatar_url": constants.QINIU_DOMIN_PREFIX + avatar_pic_url})


# 修改密码逻辑实现
@profile_blu.route("/pass_info", methods=["GET", "POST"])
@user_login_data
def pass_info():
    user = g.user
    # 不同的请求做不同的时期 get请求返回html页面
    if request.method == "GET":
        return render_template("news/user_pass_info.html")

    # post请求进行密码的修改
    # 1. 获取参数    old_password(旧密码)  new_password(新密码)
    old_password = request.json.get("old_password")
    new_password = request.json.get("new_password")

    # 2. 校验参数  参数是否都有，对比输入旧密码是否和数据库一致
    if not all([old_password, new_password]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    if not user.check_passowrd(old_password):
        return jsonify(errno=RET.PWDERR, errmsg="旧密码输入错误")

    # 3. 将数据库内密码改为新密码
    user.password = new_password

    return jsonify(errno=RET.OK, errmsg="保存成功")


# 用户收藏逻辑实现
@profile_blu.route("/collection")
@user_login_data
def user_collection():
    user = g.user
    # 获取参数 page(当前页数)
    page = request.args.get("page", "1")

    # 判断参数
    try:
        page = int(page)
    except Exception as e:
        current_app.logger.error(e)
        page = 1

    # 从数据库中取出收藏的新闻数据
    new_list = []
    total_page = 1
    current_page = 1
    try:
        paginate = user.collection_news.paginate(page, constants.USER_COLLECTION_MAX_NEWS, False)
        # 获取查询出来的数据
        new_list = paginate.items  # 新闻列表数据
        total_page = paginate.pages  # 获取总页数
        current_page = paginate.page  # 当前页数
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据查询失败")

    # 将取出的数据转为字典
    new_dict_li = []
    for news in new_list:
        new_dict_li.append(news.to_basic_dict())

    data = {
        "total_page": total_page,
        "current_page": current_page,
        "collections": new_dict_li
    }

    return render_template("news/user_collection.html", data=data)


# 用户发布新闻逻辑实现
@profile_blu.route("/news_release", methods=["GET", "POST"])
@user_login_data
def news_release():
    user = g.user
    # 不同的请求做不同的时期 get请求返回html页面
    if request.method == "GET":

        # 修改新闻分类为真实数据
        categories = Category.query.all()

        category_dict_li = []
        for category in categories:
            category_dict_li.append(category.to_dict())

        # 把名为最新的分类去掉
        category_dict_li.pop(0)

        data = {
            "categories": category_dict_li
        }

        return render_template("news/user_news_release.html", data=data)

    # post请求进行用户发布新闻
    # 1. 获取参数 title(新闻标题)  category_id(新闻分类——id)  digset(新闻摘要)  index_image(索引图片)  content(新闻内容)

    title = request.form.get("title")
    category_id = request.form.get("category_id")
    digset = request.form.get("digset")
    index_image = request.files.get("index_image")
    content = request.form.get("content")
    source = "个人发布"

    # 2. 校验参数
    if not all([title, category_id, digset, index_image, content]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    try:
        category_id = int(category_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    # 3. 读取上传的图片,将上传的图片保存到七牛云
    try:  # 将图片转为二进制
        index_image_data = index_image.read()
        # 将图片保存到七牛云
        key = storage(index_image_data)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.THIRDERR, errmsg="图片上传失败")

    # 4. 建立news模型
    news = News()
    news.title = title
    news.category_id = category_id
    news.digest = digset
    news.source = source
    news.index_image_url = constants.QINIU_DOMIN_PREFIX + key
    news.content = content
    news.user_id = user.id
    news.status = 1

    # 将数据保存到数据库
    try:
        db.session.add(news)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="保存数据失败")

    # 5. 返回成功
    return jsonify(errno=RET.OK, errmsg="发布成功")


# 用户收藏逻辑实现
@profile_blu.route("/news_list")
@user_login_data
def user_news_list():
    user = g.user

    # 获取参数 page(当前页数)
    page = request.args.get("page", "1")

    # 判断参数
    try:
        page = int(page)
    except Exception as e:
        current_app.logger.error(e)
        page = 1

    # 从数据库中取出收藏的新闻数据
    new_list = []
    total_page = 1
    current_page = 1
    try:
        paginate = News.query.filter(News.user_id == user.id).paginate(page, constants.USER_COLLECTION_MAX_NEWS, False)
        # 获取查询出来的数据
        new_list = paginate.items  # 新闻列表数据
        total_page = paginate.pages  # 获取总页数
        current_page = paginate.page  # 当前页数
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据查询失败")

    # 将取出的数据转为字典
    new_dict_li = []
    for news in new_list:
        new_dict_li.append(news.to_review_dict())

    data = {
        "total_page": total_page,
        "current_page": current_page,
        "news_list": new_dict_li
    }

    return render_template("news/user_news_list.html", data=data)


