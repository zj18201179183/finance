from finance.basic import common_response
from utils.token import token_util
from django.core.files.storage import FileSystemStorage
from django.http import HttpResponse
from .models import *


def login_required(func):
    """ 登录检查装饰器 """
    def decorate(cls, request, **kwargs):
        token = request.META.get("HTTP_AUTHORIZATION")
        if token:
            # 获取用户id
            uid = token_util.get_user_id_from_token(token)
            if uid:
                kwargs['payload'] = {'user_id':uid}
                return func(cls, request, **kwargs)

            else:
                return common_response(code=500, msg="Token Invalid")

        else:
            return common_response(code=500, msg="Please login first")

    return decorate


def is_logined(request):
    """ 检查是否登录, 返回(True, user_id)为已登录，(False, 0)为未登录 """
    token = request.META.get("HTTP_AUTHORIZATION")

    if token:
        # 获取用户id
        uid = token_util.get_user_id_from_token(token)

        if uid:
            return (True, uid)
        else:
            return (False, 0)

    else:
        return (False, 0)


# 给上传的图片重命名
class ImageStorage(FileSystemStorage):
    from django.conf import settings

    def __init__(self, location=settings.MEDIA_ROOT, base_url=settings.MEDIA_URL):
        # 初始化
        super(ImageStorage, self).__init__(location, base_url)

    # 重写 _save方法
    def _save(self, name, content):
        # name为上传文件名称
        import os, time, random
        # 文件扩展名
        ext = os.path.splitext(name)[1]
        # 文件目录
        d = os.path.dirname(name)
        # 定义文件名，年月日时分秒随机数
        fn = time.strftime('%Y%m%d%H%M%S')
        fn = fn + '_%d' % random.randint(0, 100)
        # 重写合成文件名
        name = os.path.join(d, fn + ext)
        # 调用父类方法
        return super(ImageStorage, self)._save(name, content)


# 验证用户权限
def has_permission(user_obj, view, method):
    if not user_obj.group.permission.filter(api_name=view, method=method):
        return False
    return True
