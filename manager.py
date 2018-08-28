"""
项目配置信息:
1.mysql数据库
2.配置redis: 存储session,图片验证码,短信验证码,或者缓存操作.
3.session: 用来保存用户的登陆状态
4.csrf配置: 主要对以下请求方式做保护:'POST', 'PUT', 'PATCH', 'DELETE'
5.日志文件配置
6.数据库迁移配置

"""""
import logging
import random
from datetime import datetime,timedelta

from flask import current_app
from flask_script import Manager
from flask_migrate import Migrate,MigrateCommand

from info import create_app,db,models #需要导入models,迁移的时候,知道有该文件存在

#调用方法,获取完整app
from info.models import User

app = create_app("develop")

#配置数据库迁移
manager = Manager(app,db)
Migrate(app,db)
manager.add_command("db",MigrateCommand)

# 使用的flask_script中的装饰器,目的: 可以动态通过命令调用方法,
# 参数1: 传递参数的名称,  参数2: 表示参数1的解释说明, 参数:destination,目标值,放在方法的形参
@manager.option('-u', '--username', dest='username')
@manager.option('-p', '--password', dest='password')
def create_superuser(username, password):

    #创建管理员对象
    admin = User()

    #设置属性
    admin.nick_name = username
    admin.mobile = username
    admin.password = password
    admin.is_admin = True

    #添加到数据库
    try:
        db.session.add(admin)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        return "添加失败"

    return "添加成功"


#添加测试用户
@manager.option('-t', '--test', dest='test')
def add_test_user(test):

    #定义用户列表容器
    user_list = []

    for i in range(0,10000):
        #创建用户对象
        user = User()

        #设置属性
        user.nick_name = "137%08d"%i
        user.mobile = "137%08d"%i
        user.password_hash = "pbkdf2:sha256:50000$2MEUTpZk$271ff871ca43bfe1c36e930a7d66b8fc8c620e309c4dc187a7fcab229a7da9cf"
        user.is_admin = False

        #设置用户随机登陆时间,获取当前时间 - 31天随机描述, 得到31天的活跃用户
        user.last_login = datetime.now() - timedelta(seconds=random.randint(0,3600*24*31))


        #添加用户列表
        user_list.append(user)

    #添加到数据库
    try:
        db.session.add_all(user_list)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        return "失败"

    return "成功"


if __name__ == '__main__':
    manager.run()