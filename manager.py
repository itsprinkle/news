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
from flask import current_app
from flask_script import Manager
from flask_migrate import Migrate,MigrateCommand

from info import create_app,db,models #需要导入models,迁移的时候,知道有该文件存在

#调用方法,获取完整app
app = create_app("develop")

#配置数据库迁移
manager = Manager(app,db)
Migrate(app,db)
manager.add_command("db",MigrateCommand)

if __name__ == '__main__':
    manager.run()