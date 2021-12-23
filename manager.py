from info import create_app, db, models
from flask_script import Manager
from flask_migrate import Migrate, MigrateCommand
import pymysql

from info.models import User

pymysql.install_as_MySQLdb()

# 通过指定的配置名字创建对应的app
app = create_app('development')
manager = Manager(app)
# 将app与db关联static
Migrate(app, db)
# 将数据库迁移命令添加到manager中
manager.add_command('db', MigrateCommand)


# 定义创建超级管理员函数，通过命令行创建
@manager.option("-n", "-name", dest="name")
@manager.option("-p", "-password", dest="password")
def createsuperuser(name, password):
    if not all([name, password]):
        print("参数不足")

    user = User()
    user.nick_name = name
    user.mobile = name
    user.password = password
    user.is_admin = True

    try:
        db.session.add(user)
        db.session.commit()
    except Exception as e:
        print(e)
        db.session.rollback()


if __name__ == "__main__":
    manager.run()
