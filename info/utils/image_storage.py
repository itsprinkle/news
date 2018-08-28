from qiniu import Auth, put_file, etag,put_data
import qiniu.config
#需要填写你的 Access Key 和 Secret Key
access_key = 'v3n5FPnRvLujRroKe3X9FxjMSgtWCmMWBeharusu'
secret_key = 'd3uJUlaQ9iKh0b5XkhU-Tlx5hjrDiWDDeHA4xotw'

def image_storage(image_data):
    #构建鉴权对象
    q = Auth(access_key, secret_key)

    #要上传的空间
    bucket_name = 'info11'

    #上传到七牛后保存的文件名,如果不指定名称那么由七牛云维护
    key = None

    #生成上传 Token，可以指定过期时间等
    token = q.upload_token(bucket_name, key, 3600)

    #要上传文件的本地路径
    # localfile = './sync/bbb.jpg'
    ret, info = put_data(token, key, image_data)

    #如果上传成功返回图片名称, 否则返回空字符串
    if info.status_code == 200:
        return ret.get("key")
    else:
        return ""

# 为了在当前文件运行测试上传
# if __name__ == '__main__':
#
#     with open('./11.jpg','rb') as file:
#         image_name =  image_storage(file.read())
#         if image_name:
#             print("上传成功")
#         else:
#             print("上传失败")



