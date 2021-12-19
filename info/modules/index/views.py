

from . import index_blu
from flask import render_template
from flask import current_app
from flask import session

from ... import constants
from ...models import User, News, Category
from flask import request
from flask import jsonify

from ...utils.response_code import RET


@index_blu.route('/')
def index():
    # 页面右上角是否登陆功能实现
    # 取出用户id
    user_id = session.get("user_id", None)
    # 如果用户id存在，尝试从数据库中取出用户模型
    user = None
    if user_id:
        try:
            user = User.query.get(user_id)
        except Exception as e:
            current_app.logger.error(e)

    # 点击排行功能实现
    # 1. 从数据库取出点击量最多的10条数据
    news_list = []
    try:
        news_list = News.query.order_by(News.clicks.desc()).limit(constants.CLICK_RANK_MAX_NEWS)
    except Exception as e:
        current_app.logger.error(e)

    # 将取出的数据转为字典并保存到字典列表中
    click_news_dict = []
    for news in news_list:
        click_news_dict.append(news.to_basic_dict())

    # 取出分类模型并保存到字典列表
    categories = []
    try:
        categories = Category.query.all()
    except Exception as e:
        current_app.logger.error(e)

    category_dict_li = []
    for category in categories:
        category_dict_li.append(category)

    # 如果取出用户模型，将用户模型保存返回前端
    data = {
        "user": user.to_dict() if user else None,
        "cli_news_list": click_news_dict,
        "category_disc_li": category_dict_li
    }

    return render_template('news/index.html', data=data)


# 加载favicon.ico图标
@index_blu.route('/favicon.ico')
def favicon():
    return current_app.send_static_file('news/favicon.ico')


# 展示新闻列表数据
@index_blu.route('/news_list')
def news_list():
    """
    1. 获取参数 cid(分类id，category表) page(页数，默认不传获取第一页)  per_page(每页多少条数据,默认不传10条)
    2. 校验参数 校验传入的参数是否符合条件
    3. 从数据库获取新闻数据
    :return:
    """
    # 1. 获取参数 cid(分类id，category表) page(页数，默认不传获取第一页)  per_page(每页多少条数据,默认不传10条)
    cid = request.args.get("cid", "1")
    page = request.args.get("page", "1")
    per_page = request.args.get("per_page", "10")

    # 2. 校验参数 校验传入的参数是否符合条件
    # 将参数都转为int类型，防止用户传入其他类型参数
    try:
        cid = int(cid)
        page = int(page)
        per_page = int(per_page)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    # 校验查询的是否是最新页面数据 （cid=1为最新页面数据） 查询的不是最新页面数据需要添加条件
    filters = [News.status == 0]
    if cid != 1:  # 如果cid不为1，需要将对应页面的cid添加到查询条件
        filters.append(News.category_id == cid)

    # 3. 从数据库获取新闻数据
    try:    # *filter和*args作用相同
        paginates = News.query.filter(*filters).order_by(News.create_time.desc()).paginate(page, per_page, False)

        # 获取查询出来的数据
        new_list = paginates.items  # 新闻列表数据
        total_page = paginates.pages  # 获取总页数
        current_page = paginates.page  # 当前页数

    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据查询失败")

    # 4. 查询到数据转换为字典返回前端
    news_dict_li = []
    for news in new_list:
        news_dict_li.append(news.to_basic_dict())

    data = {
        "new_list": news_dict_li,
        "total_page": total_page,
        "current_page": current_page
    }

    return jsonify(errno=RET.OK, errmsg="ok", data=data)