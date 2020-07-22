import os
import jwt
from datetime import datetime
from rest_framework.views import APIView
from finance.basic import common_response
from rest_framework.viewsets import ModelViewSet
from utils.tools import HASHIDS
from .models import User, Village
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
            # 获取帐套列表
            soa_list = []
            for soa_obj in user.village.soa.all():
                if soa_obj.is_shield and user.identity == 0:
                    soa_info = {
                        'id': soa_obj.id,
                        'name': soa_obj.name,
                        'date': datetime.strftime(soa_obj.date,'%Y-%m-%d')
                    }
                    soa_list.append(soa_info)
            return common_response(data={'token': token_util.generate_token({'user_id': user.id}), 'soa_list':soa_list})
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
        # village = data['village'] if 'village' in data else 0

        # 如果用户名 密码 手机号不存在的话直接返回错误
        if not username or not pwd or not phone_number :
            return common_response(code=500, msg='缺少必要信息')

        user_obj = User.objects.create(
            username=username,
            password=pwd,
            phone_number=phone_number,
            identity=identity,
            last_login=datetime.now(),
            photo=data['photo'] if 'photo' in data else '',
            village_id=user.village
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

        if 'user_id' in request.GET:
            update_user_id = request.GET['user_id']
            # 获取要修改的用户的信息
            try:
                update_user_obj = User.objects.get(id=HASHIDS.decode(update_user_id)[0])
            except User.DoesNotExist:
                return common_response(code=500, msg='要修改的用户不存在!')

            user_info = {
                'uid': HASHIDS.encode(user.id),
                'username': update_user_obj.username,
                'phone_number': update_user_obj.phone_number,
                'identity': update_user_obj.identity,
                'photo': update_user_obj.image_url(),
                'is_shield': update_user_obj.is_shield
            }
            return common_response(data=user_info)

        else:
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
                        'photo': obj.image_url(),
                        'is_shield': obj.is_shield
                    }
                    user_list.append(user_info)
            else:
                user_info = {
                    'uid': HASHIDS.encode(user.id),
                    'username': user.username,
                    'phone_number': user.phone_number,
                    'identity': user.get_identity_display(),
                    'photo': user.image_url(),
                    'is_shield': user.is_shield
                }
                user_list.append(user_info)
            data = {
                'identity': user.identity,
                'user_list': user_list
            }

            return common_response(data=data)


    def put(self, request):
        ''' 修改用户信息 '''
        # 验证用户信息
        is_log, user_id = is_logined(request)
        try:
            obj = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return common_response(code=500, msg='用户不存在!')

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

        if 'is_shield' in data and data['is_shield'] and data['is_shield'] != user_obj.is_shield:
            user_obj.is_shield = data['is_shield']

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


class VillageView(APIView):
    ''' 村庄的增删改查 '''
    def post(self, request):
        # 验证用户信息
        is_log, user_id = is_logined(request)
        try:
            obj = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return common_response(code=500, msg='用户不存在!')

        data = request.data
        if 'number' not in data or 'name' not in data:
            return common_response(code=500, msg='缺少必要参数')

        if not data['number'] or not data['name']:
            return common_response(code=500, msg='缺少必要值')

        parent_obj = data.get('parent_id', None)
        if parent_obj:
            try:
                parent_obj = Village.objects.get(id=parent_obj)
            except Village.DoesNotExist:
                return common_response(code=500, msg='父级id不存在')

        village_obj = Village.objects.create(
            number=data['number'],
            name=data['name'],
            parent=parent_obj
        )
        village_obj.save()
        return common_response(msg='True')

    def delete(self, request):
        # 验证用户信息
        is_log, user_id = is_logined(request)
        try:
            obj = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return common_response(code=500, msg='用户不存在!')

        data = request.data
        if 'v_id' not in data:
            return common_response(code=500, msg='缺少必要参数')

        if not data['v_id']:
            return common_response(code=500, msg='缺少必要值')

        try:
            village_obj = Village.objects.get(id=data['v_id'])
        except Village.DoesNotExist:
            return common_response(code=500, msg='id不存在')
        
        return common_response(msg='True')

    def put(self, request):
        # 验证用户信息
        is_log, user_id = is_logined(request)
        try:
            obj = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return common_response(code=500, msg='用户不存在!')

        data = request.data
        v_id = data.get('v_id', None)
        number = data.get('number', None)
        name = data.get('name', None)
        parent_obj = data.get('parent_id', None)
        if not v_id:
            return common_response(code=500, msg='缺少id')

        try:
            village_obj = Village.objects.get(id=data['v_id'])
        except Village.DoesNotExist:
            return common_response(code=500, msg='id不存在')

        if parent_obj:
            try:
                parent_obj = Village.objects.get(id=parent_obj)
            except Village.DoesNotExist:
                return common_response(code=500, msg='父级id不存在')
            else:
                village_obj.parent = parent_obj

        village_obj.number = number
        village_obj.name = name
        village_obj.save()
        return common_response(msg='True')

    def get(self, request):
        # 获取所有的乡镇用于修改
        # 验证用户信息
        is_log, user_id = is_logined(request)
        try:
            obj = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return common_response(code=500, msg='用户不存在!')

        village_obj = Village.objects.all()
        villages = []
        for vill_obj in village_obj:
            info = {
                'id': vill_obj.id,
                'name': vill_obj.name
            }
            villages.append(info)

        if 'info' in request.GET:
            return common_response(data=villages)
        
        if 'v_id' in request.GET:
            if not request.GET['v_id']:
                return common_response(code=500, msg='id为必要参数')
            try:
                village_obj = Village.objects.get(id=request.GET['v_id'])
            except Village.DoesNotExist:
                return common_response(code=500, msg='id不存在')

            village_info = {
                'id': village_obj.id,
                'name': village_obj.name,
                'number': village_obj.number,
                'parent': village_obj.parent
            }
            result = {
                'all_villages': villages,
                'info': village_info
            }
            return common_response(data=result)
            
            
        else:
            village_list = []
            for obj in village_obj:
                village_info = {
                    'id': obj.id,
                    'number': obj.number,
                    'name': obj.name,
                    'parent': obj.parent.name if obj.parent else '-'
                }
                village_list.append(village_info)
            return common_response(data=village_list)
