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

from info import create_app

#调用方法,获取完整app
app = create_app("product")

@app.route('/',methods=["POST","GET"])
def hello_world():

    #测试redis存储数据
    # redis_store.set('name','zhangsan')

    #使用session存储数据
    # session["age"] = "13"
    # print(session.get("age"))

    #不在使用print输出了,因为控制不了
    #使用loggin模块输出
    logging.debug('这是调试信息')
    logging.info('这是详细信息')
    logging.warning('这是警告信息')
    logging.error('这是错误信息')

    #还可以使用current_app来输出,和上面上面方式输出区别: 在控制台打印有分割线隔开,但是在文件中是一样的
    # current_app.logger.debug('这是调试信息')
    # current_app.logger.info('这是详细信息')
    # current_app.logger.warning('这是警告信息')
    # current_app.logger.error('这是错误信息')

    return "helloworld1000"

if __name__ == '__main__':
    app.run()