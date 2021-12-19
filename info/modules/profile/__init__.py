# 个人中心视图展示

from flask import Blueprint

profile_blu = Blueprint("profile", __name__, url_prefix="/user")  # url前加passport
from . import views

