import time
from datetime import datetime, timedelta

from info import constants, db
from info.models import User, News, Category
from info.modules.admin import admin_blu
from flask import request
from flask import render_template, current_app, session, redirect, url_for, g, jsonify, abort


# 新闻后台用户登陆功能实现
from info.utils.common import user_login_data
from info.utils.image_storage import storage
from info.utils.response_code import RET


@admin_blu.route('/login', methods=["GET", "POST"])
def login():

    if request.method == "GET":
        #  检查是否已经登陆，如果登陆，直接跳转到新闻后天页面
        user_id = session.get('user_id', None)   # 默认session中获取的user_id为空
        is_admin = session.get("is_admin", False)  # 默认session中获取的用户权限是普通用户
        if user_id and is_admin:   # 如果user_id和is_admin在session中有值，就直接重定向到新闻后台页面
            return redirect(url_for('admin.index'))
        return render_template('admin/login.html')

    # 1. 获取参数
    username = request.form.get("username")
    password = request.form.get("password")

    # 2. 校验参数
    if not all([username, password]):
        return render_template('admin/login.html', errmsg="参数不足")

    # 3. 从数据库获取账号密码，判断与用户输入的是否一致
    try:
        user = User.query.filter(User.mobile == username, User.is_admin == True).first()
    except Exception as e:
        current_app.logger.error(e)
        return render_template('admin/login.html', errmsg="用户名输入错误")

    if not user:
        return render_template('admin/login.html', errmsg="该用户不存在")

    # 4. 校验密码是否正确
    if not user.check_passowrd(password):
        return render_template('admin/login.html', errmsg="用户名或密码输入错误")

    # 将获取的参数保存到session中
    session['nike_name'] = user.nick_name
    session['mobile'] = user.mobile
    session['user_id'] = user.id
    session['is_admin'] = user.is_admin

    # 点击登陆重定向到新闻后台页面
    return redirect(url_for('admin.index'))


# 新闻后台页面实现
@admin_blu.route('/index')
@user_login_data
def index():
    user = g.user
    data = {
        "user": user.to_dict()
    }
    return render_template('admin/index.html', data=data)


# 退出功能
@admin_blu.route('/logout')
def login_out():
    """
    将登陆数据从session中移除
    :return:
    """
    # pop函数需要一个返回值，如果session中没有数据返回None
    session.pop("user_id", None)
    session.pop("mobile", None)
    session.pop("nike_name", None)
    session.pop("is_admin", None)

    return redirect(url_for('admin.login'))


# 新闻后台用户统计逻辑实现
@admin_blu.route('/user_count')
def user_count():
    # 用户总数
    total_count = 0
    # 从数据库获取除了管理员的用户
    try:
        total_count = User.query.filter(User.is_admin == False).count()
    except Exception as e:
        current_app.logger.error(e)

    # 用户月新增数
    mon_count = 0
    # 获取本月第一天0时0分0秒，创建时间大于该时间的即为该月新增数
    # 1. 获取当前时间
    now = time.localtime()
    # 2. 根据当前时间取出年和月并转为日期,作为本月的第一天
    mon_begin_date = datetime.strptime("%d-%02d-01" % (now.tm_year, now.tm_mon), "%Y-%m-%d")
    try:
        mon_count = User.query.filter(User.is_admin == False, User.create_time > mon_begin_date).count()
    except Exception as e:
        current_app.logger.error(e)

    # 用户日新增数
    day_count = 0
    # 获取当天0时0分0秒，创建时间大于该时间的即为该月新增数
    # 1. 获取当前时间
    now = time.localtime()
    # 2. 根据当前时间取出年和月并转为日期,作为本月的第一天
    day_begin_date = datetime.strptime("%d-%02d-%02d" % (now.tm_year, now.tm_mon, now.tm_mday), "%Y-%m-%d")
    try:
        day_count = User.query.filter(User.is_admin == False, User.create_time > day_begin_date).count()
    except Exception as e:
        current_app.logger.error(e)

    # 折线图逻辑实现 ，使用天数来统计用户活跃数
    active_time = []   # 折线图横坐标时间
    active_count = []   # 折线图纵坐标活跃数
    # 1. 获取今天0时0分0秒
    today_date = datetime.strptime("%d-%02d-%02d" % (now.tm_year, now.tm_mon, now.tm_mday), "%Y-%m-%d")
    # 2. 循环31天的用户活跃数
    for i in range(0, 31):
        # 取到某一天的0时0分0秒
        begin_date = today_date - timedelta(days=i)
        # 获取下一天的0时0分0秒
        end_date = today_date - timedelta(days=i - 1)
        # 从数据库中取出活跃数 当天的活跃数为最后登陆时间大于等于今天的开始0时0分0秒，小于第二天的0时0分0秒
        count = User.query.filter(User.is_admin == False, User.last_login >= begin_date,
                                  User.last_login < end_date).count()

        # 将查询出某一天时间和活跃数添加到时间和活跃数列表中
        active_count.append(count)
        #  将时间转为字符串
        active_time.append(begin_date.strftime("%Y-%m-%d"))

    # 反转，将最新一天展示在后面
    active_count.reverse()
    active_time.reverse()

    data = {
        "total_count": total_count,
        "mon_count": mon_count,
        "day_count": day_count,
        "active_time": active_time,
        "active_count": active_count
    }
    return render_template('admin/user_count.html', data=data)


@admin_blu.route('/user_list')
def user_list():
    # 获取参数 page(当前页数)
    page = request.args.get("page", "1")

    # 判断参数
    try:
        page = int(page)
    except Exception as e:
        current_app.logger.error(e)
        page = 1

    # 从数据库中取出收藏的新闻数据
    users = []
    total_page = 1
    current_page = 1
    try:
        paginate = User.query.filter(User.is_admin == False).order_by(User.last_login.asc())\
            .paginate(page, constants.ADMIN_USER_PAGE_MAX_COUNT, False)
        # 获取查询出来的数据
        users = paginate.items  # 新闻列表数据
        total_page = paginate.pages  # 获取总页数
        current_page = paginate.page  # 当前页数
    except Exception as e:
        current_app.logger.error(e)

    # 将取出的数据转为字典
    user_dict_li = []
    for user in users:
        user_dict_li.append(user.to_admin_dict())

    data = {
        "total_page": total_page,
        "current_page": current_page,
        "users": user_dict_li
    }
    return render_template('admin/user_list.html', data=data)


# 新闻审核页面
@admin_blu.route('/news_review')
def news_review():
    # 获取参数 page(当前页数)
    page = request.args.get("page", "1")
    # 接收搜索框内数据
    keywords = request.args.get("keywords", None)

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

    filters = [News.status != 0]
    # 如果搜索框有值，将其添加到搜索条件中
    if keywords:
        filters.append(News.title.contains(keywords))

    try:
        paginate = News.query.filter(*filters).order_by(News.create_time.desc())\
            .paginate(page, constants.ADMIN_USER_PAGE_MAX_COUNT, False)
        # 获取查询出来的数据
        new_list = paginate.items  # 新闻列表数据
        total_page = paginate.pages  # 获取总页数
        current_page = paginate.page  # 当前页数
    except Exception as e:
        current_app.logger.error(e)

    # 将取出的数据转为字典
    new_dict_li = []
    for news in new_list:
        new_dict_li.append(news.to_review_dict())

    data = {
        "total_page": total_page,
        "current_page": current_page,
        "news_list": new_dict_li
    }

    return render_template("admin/news_review.html", data=data)


# 新闻审核详情页面
@admin_blu.route('/news_review_detail/<int:news_id>')
def news_review_detail(news_id):
    news = None
    try:
        news = News.query.get(news_id)
    except Exception as e:
        current_app.logger.error(e)

    if not news:
        return render_template('admin/news_review_detail.html', errmsg="未查询到新闻")

    data = {
        "news": news.to_dict()
    }
    return render_template('admin/news_review_detail.html', data=data)


# 新闻审核通过or拒绝逻辑实现
@admin_blu.route('/news_review_action', methods=['POST'])
def news_review_action():
    # 1. 获取参数
    news_id = request.json.get("news_id")
    action = request.json.get("action")

    # 2. 校验参数
    if not all([news_id, action]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    if action not in ("accept", "reject"):
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    # 3. 数据库查询新闻id对应的数据
    try:
        news = News.query.get(news_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据库查询错误")

    if not news:
        return jsonify(errno=RET.NODATA, errmsg="未查询到数据")

    # 如果审核通过，将新闻状态改为0
    if action == "accept":
        news.status = 0
    else:      # 如果审核不通过，将新闻状态改为-1
        reason = request.json.get("reason")
        if not reason:
            return jsonify(errno=RET.PARAMERR, errmsg="请输入拒绝原因")
        news.reason = reason
        news.status = -1

    return jsonify(errno=RET.OK, errmsg="ok")


# 新闻版式编辑页面
@admin_blu.route('/news_edit')
def news_edit():
    # 获取参数page(当前页数)
    page = request.args.get("page", "1")
    # 接收搜索框内数据
    keywords = request.args.get("keywords", None)

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

    filters = [News.status == 0]
    # 如果搜索框有值，将其添加到搜索条件中
    if keywords:
        filters.append(News.title.contains(keywords))

    try:
        paginate = News.query.filter(*filters).order_by(News.create_time.desc())\
            .paginate(page, constants.ADMIN_USER_PAGE_MAX_COUNT, False)
        # 获取查询出来的数据
        new_list = paginate.items  # 新闻列表数据
        total_page = paginate.pages  # 获取总页数
        current_page = paginate.page  # 当前页数
    except Exception as e:
        current_app.logger.error(e)

    # 将取出的数据转为字典
    new_dict_li = []
    for news in new_list:
        new_dict_li.append(news.to_basic_dict())

    data = {
        "total_page": total_page,
        "current_page": current_page,
        "news_list": new_dict_li
    }

    return render_template("admin/news_edit.html", data=data)


# 新闻版式编辑详情页面
@admin_blu.route('/news_edit_detail', methods=["GET", "POST"])
def news_edit_detail():
    if request.method == "GET":
        news_id = request.args.get("news_id")
        if not news_id:
            abort(404)

        try:
            news_id = int(news_id)
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

        try:
            news = News.query.get(news_id)
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.DBERR, errmsg="数据库查询错误")

        # 查询分类数据
        categories = Category.query.all()
        category_dict_li = []
        for category in categories:
            cate_dict = category.to_dict()
            if category.id == news.category_id:
                cate_dict["is_selected"] = True
            category_dict_li.append(cate_dict)

        category_dict_li.pop(0)

        data = {
            "news": news.to_dict(),
            "categories": category_dict_li
        }

        return render_template('admin/news_edit_detail.html', data=data)

    news_id = request.form.get("news_id")
    title = request.form.get("title")
    digest = request.form.get("digest")
    content = request.form.get("content")
    index_image = request.files.get("index_image")
    category_id = request.form.get("category_id")
    # 1.1 判断数据是否有值
    if not all([title, digest, content, category_id]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数有误")

    news = None
    try:
        news = News.query.get(news_id)
    except Exception as e:
        current_app.logger.error(e)

    if not news:
        return jsonify(errno=RET.NODATA, errmsg="未查询到新闻数据")

    # 1.2 尝试读取图片
    if index_image:
        try:
            index_image = index_image.read()
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.PARAMERR, errmsg="参数有误")

        # 2. 将标题图片上传到七牛
        try:
            key = storage(index_image)
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.THIRDERR, errmsg="上传图片错误")
        news.index_image_url = constants.QINIU_DOMIN_PREFIX + key

    # 3. 设置相关数据
    news.title = title
    news.digest = digest
    news.content = content
    news.category_id = category_id

    return jsonify(errno=RET.OK, errmsg="编辑成功")


@admin_blu.route('/news_type', methods=["GET", "POST"])
def news_type():
    if request.method == "GET":
        # 查询分类数据
        categories = Category.query.all()
        category_dict_li = []
        for category in categories:
            cate_dict = category.to_dict()
            category_dict_li.append(cate_dict)

        category_dict_li.pop(0)

        data = {
            "categories": category_dict_li
        }
        return render_template('admin/news_type.html', data=data)

    # 进行分类的编辑或添加操作
    # 取参数
    category_name = request.json.get("name")
    # 如果有cid，代表是编辑操作
    category_id = request.json.get("id")

    if not category_name:
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    if category_id:
        try:
            category_id = int(category_id)
            category = Category.query.get(category_id)
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

        # 通过cid查询有值，则进行编辑操作，将数据库内name修改为cname
        category.name = category_name
    # 如果cid没有值，初始化一个分类对象，进行添加分类操作
    else:
        category = Category()
        category.name = category_name
        db.session.add(category)

    return jsonify(errno=RET.OK, errmsg="OK")

