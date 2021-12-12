from info import create_app, db, models
from flask_script import Manager
from flask_migrate import Migrate, MigrateCommand
import pymysql
pymysql.install_as_MySQLdb()

# 通过指定的配置名字创建对应的app
app = create_app('development')
manager = Manager(app)
# 将app与db关联static
Migrate(app, db)
# 将数据库迁移命令添加到manager中
manager.add_command('db', MigrateCommand)


if __name__ == "__main__":
    manager.run()

