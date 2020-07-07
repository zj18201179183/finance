from datetime import datetime
from rest_framework.views import APIView
from finance.basic import common_response
from rest_framework.viewsets import ModelViewSet
# from django.contrib.auth import authenticate
from .models import User
from rest_framework_jwt.settings import api_settings
from finance.settings import SECRET_KEY
import jwt

jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER


class UserAuthView(APIView):
    '''
    用户认证获取token
    '''

    def post(self, request, *args, **kwargs):
        username = request.data.get('username')
        password = request.data.get('password')
        try:
            user = User.objects.get(username=username, password=password)
        
        except User.DoesNotExist:
            return common_response(code=500, msg='用户不存在')

        if user:
            payload = jwt_payload_handler(user)
            return common_response(data={'token': jwt.encode(payload, SECRET_KEY)})
        else:
            return common_response(code=500, msg='用户名或密码错误!')


class UserViewSet(APIView):
    '''
    用户管理：增删改查
    '''
    def post(self, request, *args, **kwargs):
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
            last_login=datetime.now()
        )
        user_obj.save()
        return common_response(msg='True')


    def get(self, request, *args, **kwargs):
        " 获取用户列表 "
        user_obj = User.objects.all()
        user_list = []
        for obj in user_obj:
            user_info = {
                'uid': obj.id,
                'username': obj.username,
                'phone_number': obj.phone_number,
                'identity': obj.get_identity_display(),
                'photo': 'https://lin-xin.gitee.io/images/post/wms.png'
            }
            user_list.append(user_info)
        return common_response(data=user_list)


    def put(self, request, *args, **kwargs):
        ''' 修改用户信息 '''
        data = request.data
        if 'uid' not in data:
            return common_response(code=500, msg='用户id不存在')
        try:
            user_obj = User.objects.get(id=data['uid'])
        
        except User.DoesNotExist:
            return common_response(code=500, msg='用户不存在')

        if 'username' in data and data['username'] and data['username'] != user_obj.username:
            user_obj.username = data['username']

        if 'password' in data and data['password'] and data['password'] != user_obj.password:
            user_obj.password = data['password']

        if 'phone_number' in data and data['phone_number'] and data['phone_number'] != user_obj.phone_number:
            user_obj.phone_number = data['phone_number']

        if 'identity' in data and data['identity'] and data['identity'] != user_obj.identity:
            user_obj.identity = data['identity']

        user_obj.save()
        return common_response(msg='True')


    def delete(self, request, *args, **kwargs):
        ''' 删除用户 '''
        data = request.data
        if 'uid' not in data:
            return common_response(code=500, msg='用户id不存在')

        try:
            user_obj = User.objects.get(id=data['uid'])
        
        except User.DoesNotExist:
            return common_response(code=500, msg='用户不存在')

        user_obj.delete()
        return common_response(msg='True')

