# from info.modules.index import index_blu
from info import redis_store
from . import index_blu
from flask import render_template,current_app

@index_blu.route('/',methods=["POST","GET"])
def hello_world():

    #测试redis存储数据
    # redis_store.set('name','zhangsan')

    #使用session存储数据
    # session["age"] = "13"
    # print(session.get("age"))

    #不在使用print输出了,因为控制不了
    #使用loggin模块输出
    # logging.debug('这是调试信息')
    # logging.info('这是详细信息')
    # logging.warning('这是警告信息')
    # logging.error('这是错误信息')

    #还可以使用current_app来输出,和上面上面方式输出区别: 在控制台打印有分割线隔开,但是在文件中是一样的
    # current_app.logger.debug('这是调试信息')
    # current_app.logger.info('这是详细信息')
    # current_app.logger.warning('这是警告信息')
    # current_app.logger.error('这是错误信息')

    return render_template('news/index.html')

#每个浏览器去访问服务器的时候会自动发送一个GET请求,地址是:/favicon.ico
#flask中提供了一个方法send_static_file(文件A),自动寻找static目录底下的文件A
@index_blu.route('/favicon.ico')
def get_web_logo():

    return current_app.send_static_file('news/favicon.ico')