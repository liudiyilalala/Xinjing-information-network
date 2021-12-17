from flask import abort

from . import news_blu
from flask import render_template
from info.utils.common import user_login_data
from flask import g
from ... import constants, db
from ...models import News, Comment, CommentLike
from flask import current_app
from flask import request
from flask import jsonify


# 实现新闻详情页
from ...utils.response_code import RET


@news_blu.route('/<int:news_id>')
@user_login_data
def news_detail(news_id):
    # 右上角是否登陆逻辑
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

    # 查询评论数据
    comments = []
    try:
        comments = Comment.query.filter(Comment.news_id == news_id).order_by(Comment.create_time.desc()).all()
    except Exception as e:
        current_app.logger.error(e)

    comment_Likes_ids = []
    if user:
        try:
            # 是否点赞后端逻辑实现
            # 1. 查询出当前新闻的所以评论
            comment_ids = [comment.id for comment in comments]
            # 2. 再查询当前评论中哪些评论被哪些用户点赞
            comment_Likes = CommentLike.query.filter(CommentLike.comment_id.in_(comment_ids),
                                                     CommentLike.user_id == user.id).all()
            # 3. 取到所有点赞的评论id
            comment_Likes_ids = [comment_Likes.comment_id for comment_Likes in comment_Likes]
        except Exception as e:
            current_app.logger.error(e)

    comments_dict_li = []
    for comment in comments:
        # 代表没有点赞
        comment_dict = comment.to_dict()
        comment_dict["is_like"] = False
        # 判断当前遍历到的评论是否被当前用户点赞
        if comment.id in comment_Likes_ids:
            comment_dict["is_like"] = True
        comments_dict_li.append(comment_dict)

    data = {
        "user": user.to_dict() if user else None,
        "cli_news_list": click_news_dict,
        "news": news.to_dict(),
        "is_collected": is_collected,
        "comments": comments_dict_li
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


# 评论新闻的后端实现
@news_blu.route('/news_comment', methods=["POST"])
@user_login_data
def news_comment():
    """
    1. 获取参数 news_id(新闻的id)  comment(评论内容) parent_id(回复的评论的id，可能没有)
    2. 校验参数
    3. 获取新闻是否存在
    4. 建立评论comment模型，将评论保存到数据库中
    5. 将数据返回前端
    :return:
    """
    # 判断用户是否登陆
    user = g.user
    if not user:
        return jsonify(errno=RET.SESSIONERR, errmsg="用户未登陆")
    # 1. 获取参数 news_id(新闻的id)  comment(评论内容) parent_id(回复的评论的id，可能没有)
    news_id = request.json.get("news_id")
    comment_content = request.json.get("comment")
    parent_id = request.json.get("parent_id")

    # 2. 校验参数
    if not all([news_id, comment_content]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    try:
        news_id = int(news_id)
        if parent_id:
            parent_id = int(parent_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    # 3. 获取新闻是否存在
    try:
        news = News.query.get(news_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据库查询错误")

    if not news:
        return jsonify(errno=RET.NODATA, errmsg="新闻不存在")

    # 4. 建立评论comment模型，将评论保存到数据库中
    comment = Comment()
    comment.user_id = user.id
    comment.news_id = news_id
    comment.content = comment_content
    if parent_id:
        comment.parent_id = parent_id

    # 保存数据到数据库
    try:
        db.session.add(comment)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()

    return jsonify(errno=RET.OK, errmsg="OK", data=comment.to_dict())


# 评论点赞后端实现
@news_blu.route('/comment_like', methods=["POST"])
@user_login_data
def comment_like():
    """
    1. 获取参数 comment_id(评论的id)  news_id(新闻的id)  action(点赞操作：add点赞 ，remove取消点赞)
    2. 校验参数
    3. 根据查找评论和用户id来创建点赞该评论的点赞模型
    4. 将点赞添加到数据库或从数据库取消点赞
    :return:
    """
    # 判断用户是否登陆
    user = g.user
    if not user:
        return jsonify(errno=RET.SESSIONERR, errmsg="用户未登陆")

    # 1. 获取参数 comment_id(评论的id)  news_id(新闻的id)  action(点赞操作：add点赞 ，remove取消点赞)
    news_id = request.json.get("news_id")
    comment_id = request.json.get("comment_id")
    action = request.json.get("action")

    # 2. 校验参数
    if not all([news_id, comment_id, action]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    try:
        news_id = int(news_id)
        comment_id = int(comment_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    if action not in ("add", "remove"):
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    #  获取评论是否存在
    try:
        comment = Comment.query.get(comment_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据库查询错误")

    if not comment:
        return jsonify(errno=RET.NODATA, errmsg="评论不存在")

    # 3. 根据action状态，查找评论和用户id获取是否点赞，来创建点赞模型
    if action == "add":
        # 根据前端的add请求，在数据库查找该评论是否被点赞
        comment_like_model = CommentLike.query.filter(CommentLike.user_id == user.id,
                                                         CommentLike.comment_id == comment_id).first()
        # 如果没有点赞，则创建点赞模型，将点赞添加到数据库
        if not comment_like_model:
            comments_like = CommentLike()
            comments_like.comment_id = comment_id
            comments_like.user_id = user.id
            db.session.add(comments_like)
            comment.like_count += 1
    # 如果前端返回的remove请求，在数据库查找该评论是否被点赞
    else:
        comment_like_model = CommentLike.query.filter(CommentLike.user_id == user.id,
                                                         CommentLike.comment_id == comment_id).first()
        # 如果已经点赞，删除点赞操作
        if comment_like_model:
            db.session.delete(comment_like_model)
            comment.like_count -= 1
    try:
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg="操作失败")

    return jsonify(errno=RET.OK, errmsg="ok")

