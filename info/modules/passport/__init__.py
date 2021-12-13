# 登陆注册的逻辑实现
from flask import Blueprint

passport_blu = Blueprint("passport", __name__, url_prefix="/passport")  # url前加passport
from . import views

