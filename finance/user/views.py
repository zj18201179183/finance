import os
import jwt
from datetime import datetime
from rest_framework.views import APIView
from finance.basic import common_response
from rest_framework.viewsets import ModelViewSet
from utils.tools import HASHIDS
from .models import User
from .func import login_required, is_logined
from rest_framework_jwt.settings import api_settings
from django.contrib.auth import authenticate, login, logout
from django.conf import settings
from utils.token import token_util


class UserAuthView(APIView):
    '''
    用户认证获取token
    '''
    def post(self, request):
        ''' 用户登陆 '''
        username = request.data.get('username')
        password = request.data.get('password')

        try:
            user = User.objects.get(username=username, password=password)
        
        except User.DoesNotExist:
            return common_response(code=500, msg='用户不存在')

        if user.identity != 0 and user.is_shield:
            return common_response(code=500, msg='该用户已被屏蔽,无法登陆,请联系管理员!')

        if user:
            # 记住登陆信息
            login(request, user)
            return common_response(data={'token': token_util.generate_token({'user_id': user.id})})
        else:
            return common_response(code=500, msg='用户名或密码错误!')


    def put(self, request):
        ''' 用户退出 '''
        print(request.user)
        return common_response(msg='Succ')


class UserViewSet(APIView):
    '''
    用户管理：增删改查
    '''
    def post(self, request):
        # 验证用户信息
        is_log, user_id = is_logined(request)
        try:
            obj = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return common_response(code=500, msg='用户不存在!')
        # 用户身份非管理员的话直接退出
        if obj.identity!=0:
            return common_response(code=500, msg='当前身份无法添加用户,请切换管理员身份！')

        # 创建用户
        data = request.data
        username = data['username'] if 'username' in data else ''
        pwd = data['password'] if 'password' in data else ''
        phone_number = data['phone_number'] if 'phone_number' in data else ''
        identity = data['identity'] if 'identity' in data else 0

        # 如果用户名 密码 手机号不存在的话直接返回错误
        if not username or not pwd or not phone_number:
            return common_response(code=500, msg='缺少必要信息')

        user_obj = User.objects.create(
            username=username,
            password=pwd,
            phone_number=phone_number,
            identity=identity,
            last_login=datetime.now(),
            photo=data['photo'] if 'photo' in data else ''
        )
        user_obj.save()
        return common_response(msg='True')


    def get(self, request):
        " 获取用户列表 "
        # 验证用户信息
        is_log, user_id = is_logined(request)
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return common_response(code=500, msg='用户不存在!')
        # 根据用户身份展示不同的用户列表
        user_list = []
        if user.identity==0:
            user_obj = User.objects.all()
            for obj in user_obj:
                user_info = {
                    'uid': HASHIDS.encode(obj.id),
                    'username': obj.username,
                    'phone_number': obj.phone_number,
                    'identity': obj.get_identity_display(),
                    'photo': obj.image_url()
                }
                user_list.append(user_info)
        else:
            user_info = {
                'uid': HASHIDS.encode(user.id),
                'username': user.username,
                'phone_number': user.phone_number,
                'identity': user.get_identity_display(),
                'photo': user.image_url()
            }
            user_list.append(user_info)
        data = {
            'identity': user.identity,
            'user_list': user_list
        }

        return common_response(data=data)


    def put(self, request):
        ''' 修改用户信息 '''
        data = request.data
        update_user_id = HASHIDS.decode(data['uid'])[0]
        # 验证登陆用户信息
        is_log, user_id = is_logined(request)
        try:
            login_user_obj = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return common_response(code=500, msg='用户不存在')
        # 用户为管理员则可以修改任何用户 否则只能修改自己
        if login_user_obj.identity != 0 and user_id != update_user_id:
            return common_response(code=500, msg='以您当前的身份无法只能修改自己的信息!')

        # 获取修改用户的信息
        try:
            user_obj = User.objects.get(id=update_user_id)
        except User.DoesNotExist:
            return common_response(code=500, msg='用户不存在')

        if 'password' in data and data['password'] and data['password'] != user_obj.password:
            user_obj.password = data['password']

        if 'phone_number' in data and data['phone_number'] and data['phone_number'] != user_obj.phone_number:
            user_obj.phone_number = data['phone_number']

        if 'identity' in data and data['identity'] and data['identity'] != user_obj.identity:
            user_obj.identity = data['identity']

        if 'photo' in data and data['photo']:
            # 删除文件
            os.remove(settings.BASE_DIR+user_obj.photo.url)
            user_obj.photo = data['photo']

        user_obj.save()
        return common_response(msg='True')


    def delete(self, request):
        ''' 删除用户 '''
        # 验证用户信息
        is_log, user_id = is_logined(request)
        try:
            user_obj = User.objects.get(id=user_id)
        
        except User.DoesNotExist:
            return common_response(code=500, msg='用户不存在')

        # 用户身份非管理员的话直接退出
        if user_obj.identity!=0:
            return common_response(code=500, msg='当前身份无法删除用户,请切换管理员身份！')

        # 删除文件
        os.remove(settings.BASE_DIR+user_obj.photo.url)
        user_obj.delete()
        return common_response(msg='True')

