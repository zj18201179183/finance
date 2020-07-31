import os
import jwt
from datetime import datetime
from rest_framework.views import APIView
from finance.basic import common_response
from rest_framework.viewsets import ModelViewSet
from utils.tools import HASHIDS
from .models import User, Village, Group, Permission
from .func import login_required, is_logined, has_permission
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

        if not user.is_admin and user.is_shield:
            return common_response(code=500, msg='该用户已被屏蔽,无法登陆,请联系管理员!')

        if user:
            if user.is_admin:
                return common_response(data={'token': token_util.generate_token({'user_id': user.id})})

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


class GroupView(APIView):
    def post(self, request):
        is_log, user_id = is_logined(request)
        try:
            user_obj = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return common_response(code=500, msg='用户不存在!')
        # 用户身份非管理员的话直接退出
        if not user_obj.is_admin:
            return common_response(code=500, msg='当前身份无法添加用户,请切换管理员身份！')
        
        data = request.data
        group_name = data.get('group_name', '')
        permissions = data.get('permission_ids', '')
        if not group_name or not permissions:
            return common_response(code=500, msg='缺少必要参数')
        
        group_obj = Group.objects.create(
            group_name = group_name
        )
        # 添加用户权限
        permission_list = permissions.strip(',').split(',')
        permission_obj = Permission.objects.filter(id__in=permission_list)
        group_obj.permission.add(*permission_obj)
        group_obj.save()
        return common_response(msg='True')

    def put(self, request):
        is_log, user_id = is_logined(request)
        try:
            user_obj = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return common_response(code=500, msg='用户不存在!')
        # 用户身份非管理员的话直接退出
        if not user_obj.is_admin:
            return common_response(code=500, msg='当前身份无法添加用户,请切换管理员身份！')

        data = request.data
        group_id = data.get('group_id', '')
        if not group_id:
            return common_response(code=500, msg='缺少必要id')
        try:
            group_obj = Group.objects.get(id=group_id)
        except Group.DoesNotExist:
            return common_response(code=500, msg='分组id不存在')

        group_name = data.get('group_name', group_obj.group_name)
        permission_ids = data.get('permission_ids', '')
        group_obj.group_name = group_name
        if permission_ids:
            permission_list = permission_ids.strip(',').split(',')
            group_obj.permission.clear()
            group_obj.permission.set(permission_list)

        group_obj.save()
        return common_response(msg='True')

    def get(self, request):
        is_log, user_id = is_logined(request)
        try:
            user_obj = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return common_response(code=500, msg='用户不存在!')
        # 用户身份非管理员的话直接退出
        if not user_obj.is_admin:
            return common_response(code=500, msg='当前身份无法添加用户,请切换管理员身份！')

        group_id = request.GET.get('group_id', '')
        data_type = request.GET.get('type', 'list')

        # 获取所有的权限
        permission_list = []
        for permission_obj in Permission.objects.all():
            permission_info = {
                'id': permission_obj.id,
                'permission_name': permission_obj.permission_name
            }
            permission_list.append(permission_info)

        # 获取详情
        if group_id:
            try:
                group_obj = Group.objects.get(id=group_id)
            except Group.DoesNotExist:
                return common_response(code=500, msg='分组id不存在')
            
            get_info = {
                'group_name': group_obj.group_name,
                'permission_ids': [per_obj.id for per_obj in group_obj.permission.all()]
            }
            result = {
                'info': get_info,
                'permission_list': permission_list
            }
            return common_response(data=result)

        # 获取所有的分组
        if data_type == 'list':
            result = []
            for group_obj in Group.objects.all():
                group_info = {
                    'id': group_obj.id,
                    'group_name': group_obj.group_name
                }
                result.append(group_info)
            return common_response(data=result)

        if data_type == 'permission':
            return common_response(data=permission_list)


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
        if not obj.is_admin:
            return common_response(code=500, msg='当前身份无法添加用户,请切换管理员身份！')

        # 创建用户
        data = request.data
        username = data['username'] if 'username' in data else ''
        pwd = data['password'] if 'password' in data else ''
        phone_number = data['phone_number'] if 'phone_number' in data else ''
        village_id = data['village_id'] if 'village_id' in data else 0
        group_id = data['group_id'] if 'group_id' in data else 0

        # 如果用户名 密码 手机号不存在的话直接返回错误
        if not username or not pwd or not phone_number or not village_id or not group_id:
            return common_response(code=500, msg='缺少必要信息')

        try:
            village_obj = Village.objects.get(id=village_id)
        except Village.DoesNotExist:
            return common_response(code=500, msg='该村庄不存在')

        try:
            group_obj = Group.objects.get(id=group_id)
        except Group.DoesNotExist:
            return common_response(code=500, msg='分组不存在')

        user_obj = User.objects.create(
            username=username,
            password=pwd,
            phone_number=phone_number,
            photo=data['photo'] if 'photo' in data else '',
            village=village_obj,
            group=group_obj
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

        # 用户身份非管理员的话直接退出
        if not user.is_admin:
            return common_response(code=500, msg='当前身份无法删除用户,请切换管理员身份！')

        if 'user_id' in request.GET:
            update_user_id = request.GET['user_id']
            if not update_user_id:
                return common_response(code=500, msg='要修改的用户id不存在!')
            # 获取要修改的用户的信息
            try:
                update_user_obj = User.objects.get(id=update_user_id)
            except User.DoesNotExist:
                return common_response(code=500, msg='要修改的用户不存在!')

            user_info = {
                'uid': update_user_obj.id,
                'username': update_user_obj.username,
                'password': update_user_obj.password,
                'phone_number': update_user_obj.phone_number,
                'photo': update_user_obj.image_url(),
                'is_shield': update_user_obj.is_shield,
                'village': update_user_obj.village.id if update_user_obj.village else '',
                'group': update_user_obj.group.id if update_user_obj.group else '',
            }
            return common_response(data=user_info)

        else:
            user_list = []
            for obj in User.objects.filter(is_admin=False).all():
                user_info = {
                    'uid': obj.id,
                    'username': obj.username,
                    'phone_number': obj.phone_number,
                    'photo': obj.image_url(),
                    'is_shield': obj.is_shield,
                    'village': obj.village.name if obj.village else '',
                    'group': obj.group.group_name if obj.group else '',
                }
                user_list.append(user_info)

            return common_response(data=user_list)


    def put(self, request):
        ''' 修改用户信息 '''
        # 验证用户信息
        is_log, user_id = is_logined(request)
        try:
            obj = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return common_response(code=500, msg='用户不存在!')

        # 用户为管理员则可以修改任何用户 否则只能修改自己
        if not obj.is_admin:
            return common_response(code=500, msg='当前身份没有权限')

        data = request.data
        update_user_id = data['uid']
        # 获取修改用户的信息
        try:
            user_obj = User.objects.get(id=update_user_id)
        except User.DoesNotExist:
            return common_response(code=500, msg='用户不存在')

        if 'password' in data and data['password'] and data['password'] != user_obj.password:
            user_obj.password = data['password']

        if 'phone_number' in data and data['phone_number'] and data['phone_number'] != user_obj.phone_number:
            user_obj.phone_number = data['phone_number']

        if 'is_shield' in data and data['is_shield'] and data['is_shield'] != user_obj.is_shield:
            user_obj.is_shield = data['is_shield']

        village_id = data.get('village_id', user_obj.village.id)
        group_id = data.get('group_id', user_obj.group.id)
        try:
            village_obj = Village.objects.get(id=village_id)
        except Village.DoesNotExist:
            pass
        else:
            user_obj.village = village_obj

        try:
            group_obj = Group.objects.get(id=group_id)
        except Group.DoesNotExist:
            pass
        else:
            user_obj.group = group_obj

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
        if not user_obj.is_admin:
            return common_response(code=500, msg='当前身份无法删除用户,请切换管理员身份！')

        data = request.data
        remove_user_id = data.get('uid', '')
        if not remove_user_id:
            return common_response(code=500, msg='缺少用户id')

        try:
            remove_user_obj = User.objects.get(id=remove_user_id)
        
        except User.DoesNotExist:
            return common_response(code=500, msg='用户不存在')

        # 删除文件
        if remove_user_obj.photo:
            os.remove(settings.BASE_DIR+remove_user_obj.photo.url)
        remove_user_obj.delete()
        return common_response(msg='True')


class UserShieldView(APIView):
    def put(self, request):
        # 验证用户信息
        is_log, user_id = is_logined(request)
        try:
            obj = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return common_response(code=500, msg='用户不存在!')

        # 是否有权限
        if not has_permission(obj, 'UserShield', 'PUT'):
            return common_response(code=500, msg='您没有操作权限')

        # 修改权限
        data = request.data
        shield_user = data.get('user_id', 0)
        try:
            user_obj = User.objects.get(id=shield_user)
        except User.DoesNotExist:
            return common_response(code=500, msg='用户不存在')

        user_obj.is_shield = True
        user_obj.save()
        return common_response(msg='succ')


class VillageView(APIView):
    ''' 村庄的增删改查 '''
    def post(self, request):
        # 验证用户信息
        is_log, user_id = is_logined(request)
        try:
            obj = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return common_response(code=500, msg='用户不存在!')

        if not obj.is_admin:
            return common_response(code=500, msg='没有权限')

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

        if not obj.is_admin:
            return common_response(code=500, msg='没有权限')

        data = request.data
        if 'v_id' not in data:
            return common_response(code=500, msg='缺少必要参数')

        if not data['v_id']:
            return common_response(code=500, msg='缺少必要值')

        try:
            village_obj = Village.objects.get(id=data['v_id'])
        except Village.DoesNotExist:
            return common_response(code=500, msg='id不存在')

        village_obj.delete()
        
        return common_response(msg='True')

    def put(self, request):
        # 验证用户信息
        is_log, user_id = is_logined(request)
        try:
            obj = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return common_response(code=500, msg='用户不存在!')
        
        if not obj.is_admin:
            return common_response(code=500, msg='没有权限')

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

        if not obj.is_admin:
            return common_response(code=500, msg='没有权限')

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
