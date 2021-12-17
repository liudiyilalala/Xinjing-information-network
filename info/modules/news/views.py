from flask import abort

from . import news_blu
from flask import render_template
from info.utils.common import user_login_data
from flask import g
from ... import constants
from ...models import News
from flask import current_app
from flask import request
from flask import jsonify


# 实现新闻详情页
from ...utils.response_code import RET


@news_blu.route('/<int:news_id>')
@user_login_data
def news_detail(news_id):
    user = g.user
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

    # 新闻详情页数据展示，根据news_id查找数据库内容
    news = None
    try:
        news = News.query.get(news_id)
    except Exception as e:
        current_app.logger.error(e)

    # 如果没有查到数据，返回404
    if not news:
        abort(404)

    # 查到数据，新闻点击数+1
    news.clicks += 1

    # 是否收藏逻辑实现。如果登陆用户显示收藏，则is_collected显示True
    is_collected = False
    if user:  # 用户登录
        if news in user.collection_news:
            is_collected = True

    data = {
        "user": user.to_dict() if user else None,
        "cli_news_list": click_news_dict,
        "news": news.to_dict(),
        "is_collected": is_collected
    }

    return render_template("news/detail.html", data=data)


# 收藏以及取消收藏后端逻辑实现
@news_blu.route('/news_collect', methods=["POST"])
@user_login_data
def news_collect():
    """
    1. 获取参数 new_id(要收藏的新闻id)
    2. 校验参数 参数是否存在
    3. 查询新闻是否存在，并判断新闻是否已经收藏
    4. 进行收藏或取消收藏操作
    :return:
    """
    # 获取用户模型
    user = g.user
    if not user:
        return jsonify(errno=RET.SESSIONERR, errmsg="用户未登陆")

    # 1. 获取参数 new_id(要收藏的新闻id)  action（指定两个值 "collect" "cancel_collect"代表收藏或者取消收藏)
    news_id = request.json.get("news_id")
    action = request.json.get("action")

    # 2. 校验参数 参数是否存在
    if not all([action, news_id]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    if action not in ("collect", "cancel_collect"):
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    # 3. 查询新闻是否存在，并判断新闻是否已经收藏
    try:
        news = News.query.get(news_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据库查询错误")

    if not news:
        return jsonify(errno=RET.NODATA, errmsg="新闻不存在")

    # 4. 进行收藏或取消收藏操作
    if action == "cancel_collect":
        # 取消收藏
        if news in user.collection_news:
            user.collection_news.remove(news)
    else:
        # 收藏操作
        if news not in user.collection_news:
            user.collection_news.append(news)

    return jsonify(errno=RET.OK, errmsg="操作成功")
