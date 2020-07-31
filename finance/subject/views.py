import json
from decimal import Decimal
from datetime import date, datetime
from rest_framework.views import APIView
from .models import *
from .func import get_all_subject
from user.models import User
from user.func import is_logined, has_permission
from subject.func import get_all_subject
from finance.basic import common_response
from utils.tools import HASHIDS

# Create your views here.

class SetOfAccountsView(APIView):
    ''' 设置帐套 '''
    def post(self, request):
        # 验证用户信息
        is_log, user_id = is_logined(request)
        try:
            obj = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return common_response(code=500, msg='用户不存在!')

        # 验证用户权限
        if not has_permission(obj, 'SetOfAccounts', 'POST'):
            return common_response(code=500, msg='您没有操作权限')

        data = request.data
        name = data.get('name', '')
        soa_date = data.get('date', date.today())
        if isinstance(soa_date, str):
            soa_date = datetime.strptime(soa_date, '%Y-%m-%d').date()
        if not name:
            return common_response(code=500, msg='帐套名不能为空')

        soa_obj = SetOfAccounts.objects.create(
            name=name,
            date=soa_date,
            village=obj.village
        )
        # 初始化科目余额
        for sub_obj in Subject.objects.filter(village=None):
            subjectofaccounts_obj = SubjectOfAccounts.objects.create(
                account=soa_obj,
                subject=sub_obj
            )
            subjectofaccounts_obj.save()

        soa_obj.save()
        return common_response(msg='True')

    def put(self, request):
        # 验证用户信息
        is_log, user_id = is_logined(request)
        try:
            obj = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return common_response(code=500, msg='用户不存在!')

        # 验证用户权限
        if not has_permission(obj, 'SetOfAccounts', 'PUT'):
            return common_response(code=500, msg='您没有操作权限')

        data = request.data
        soa_id = data.get('soa_id', '')
        if not soa_id:
            return common_response(code=500, msg='帐套id不能为空')

        try:
            soa_obj = SetOfAccounts.objects.get(id=soa_id)
        except SetOfAccounts.DoesNotExist:
            return common_response(code=500, msg='帐套id不存在')

        # 屏蔽帐套
        is_shield = data.get('is_shield', '')
        if is_shield:
            soa_obj.is_shield = is_shield
            soa_obj.save()
            return common_response(msg='True')

        # 修改帐套名
        name = data.get('name', '')
        if not name:
            return common_response(code=500, msg='帐套名不能为空')

        soa_obj.name = name
        soa_obj.save()
        return common_response(msg='True') 

    def get(self, request):
        # 验证用户信息
        is_log, user_id = is_logined(request)
        try:
            user_obj = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return common_response(code=500, msg='用户不存在!')

        # 验证用户权限
        if not has_permission(user_obj, 'SetOfAccounts', 'GET'):
            return common_response(code=500, msg='您没有操作权限')

        soa_id = request.GET.get('soa_id', '')
        if soa_id:
            try:
                soa_obj = SetOfAccounts.objects.get(id=soa_id)
            except SetOfAccounts.DoesNotExist:
                return common_response(code=500, msg='帐套id不存在')

            soa_info = {
                'id': soa_obj.id,
                'name': soa_obj.name,
                'date': datetime.strftime(soa_obj.date,'%Y-%m-%d')
            }
            return common_response(data=soa_info)

        get_type = request.GET.get('type', 'list')
        if get_type == 'list':
            soa_list = []
            for obj in SetOfAccounts.objects.all():
                if obj.is_shield and user_obj.identity != 0:
                    continue

                soa_info_list = {
                    'id': obj.id,
                    'name': obj.name,
                    'date': datetime.strftime(obj.date,'%Y-%m-%d')
                }
                soa_list.append(soa_info_list)
            return common_response(data=soa_list)


class SubjectView(APIView):
    ''' 科目管理 '''
    def post(self, request):
        # 验证用户信息
        is_log, user_id = is_logined(request)
        try:
            obj = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return common_response(code=500, msg='用户不存在!')

        # 验证用户权限
        if not has_permission(obj, 'Subject', 'POST'):
            return common_response(code=500, msg='您没有操作权限')

        data = request.data
        # 验证数据
        subject_num = data.get('subject_num', '')
        subject_name = data.get('subject_name', '')
        subject_father = data.get('subject_father', None)
        subject_type = data.get('subject_type', 0)
        balance_type = data.get('balance_type', 0)
        assists = data.get('assists', 0)
        soa_id = data.get('soa_id', 0)
        if not soa_id:
            return common_response(code=500, msg='缺少帐套id')

        # 数据入库
        if not subject_num and not subject_name:
            return common_response(code=500, msg='缺少必要参数')

        # 获取父级对象
        if subject_father:
            try:
                parent_obj = Subject.objects.get(id=subject_father)
            except Subject.DoesNotExist:
                return common_response(code=500, msg='上级id不存在')
            else:
                subject_father = parent_obj

        subject_obj = Subject.objects.create(
            subject_num=subject_num,
            subject_name=subject_name,
            parent=subject_father,
            subject_type=subject_type,
            balance_type=balance_type,
            can_operation=True,
            village=obj.village
        )
        # 存储多对多关联表数据
        if assists:
            # 字符串转为列表
            ass_list = assists.strip(',').split(',')
            ass_obj = Assist.objects.filter(id__in=ass_list)
            subject_obj.assist_business.add(*ass_obj)

        # 科目余额
        soa_obj = SubjectOfAccounts.objects.create(
            account_id=soa_id,
            subject=subject_obj,
            num=0,
            money=0,
            balance=0
        )

        subject_obj.save()
        soa_obj.save()
        return common_response(msg='succ')

    def delete(self, request):
        # 验证用户信息
        is_log, user_id = is_logined(request)
        try:
            obj = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return common_response(code=500, msg='用户不存在!')

        # 验证用户权限
        if not has_permission(obj, 'Subject', 'DELETE'):
            return common_response(code=500, msg='您没有操作权限')

        data = request.data
        sub_id = data.get('sub_id', 0)
        try:
            sub_obj = Subject.objects.get(id=sub_id)
        except Subject.DoesNotExist:
            return common_response(code=500, msg='ID不存在')

        # 判断当前用户是否可操作
        if not sub_obj.can_operation:
            return common_response(code=500, msg='当前科目不可操作')

        sub_obj.delete()
        return common_response(code=200)

    def put(self, request):
        # 验证用户信息
        is_log, user_id = is_logined(request)
        try:
            obj = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return common_response(code=500, msg='用户不存在!')

        # 验证用户权限
        if not has_permission(obj, 'Subject', 'PUT'):
            return common_response(code=500, msg='您没有操作权限')

        data = request.data
        # 获取项目id
        sub_id = data.get('sub_id', 0)
        if not sub_id:
            return common_response(code=500, msg='没有接收到ID')
        try:
            sub_obj = Subject.objects.get(id=sub_id)
        except Subject.DoesNotExist:
            return common_response(code=500, msg='ID不存在')

        # 判断当前用户是否可操作
        if not sub_obj.can_operation:
            return common_response(code=500, msg='当前科目不可操作')

        # 验证数据
        subject_num = data.get('subject_num', sub_obj.subject_num)
        subject_name = data.get('subject_name', sub_obj.subject_name)
        subject_father = data.get('subject_father', None)
        subject_type = data.get('subject_type', sub_obj.subject_type)
        balance_type = data.get('balance_type', sub_obj.balance_type)
        assists = data.get('assists', 0)
        # 数据入库
        if not subject_num or not subject_name:
            return common_response(code=500, msg='缺少必要参数')

        # 获取父级对象
        if subject_father:
            try:
                parent_obj = Subject.objects.get(id=subject_father)
            except Subject.DoesNotExist:
                return common_response(code=500, msg='上级id不存在')
            else:
                subject_father = parent_obj

        sub_obj.subject_num = subject_num
        sub_obj.subject_name = subject_name
        sub_obj.parent = subject_father
        sub_obj.subject_type = subject_type
        sub_obj.balance_type = balance_type

        # 修改多对多关联表数据
        if assists:
            # 字符串转为列表
            ass_list = assists.strip(',').split(',')
            sub_obj.assist_business.clear()
            sub_obj.assist_business.set(ass_list)

        sub_obj.save()
        sub_obj.subjectofaccounts.save()
        return common_response(msg='succ')

    def get(self, request):
        ''' 
            通过data_type来区分获取的数据 
                data_type为info获取相关数据(主要是获取辅助核算列表)
                data_type为list获取项目列表
            通过sub_id获取项目详情
            sub_id 优先级大于data_type
        '''
        # 验证用户信息
        is_log, user_id = is_logined(request)
        try:
            obj = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return common_response(code=500, msg='用户不存在!')

        # 验证用户权限
        if not has_permission(obj, 'Subject', 'GET'):
            return common_response(code=500, msg='您没有操作权限')

        sub_id = request.GET.get('sub_id', '')
        data_type = request.GET.get('type', 'info')

        ''' 辅助核算 '''
        ass_obj = Assist.objects.all()
        ass_list = []
        for obj in ass_obj:
            ass_info = {
                'id': obj.id,
                'name': obj.assist_name
            }
            ass_list.append(ass_info)

        ''' 所有科目 '''
        all_subjects = get_all_subject(obj)

        # 获取详情
        if sub_id:
            try:
                sub_obj = Subject.objects.get(id=sub_id)
            except Subject.DoesNotExist:
                return common_response(code=500, msg='项目id不存在')
            
            sub_info = {
                'id': sub_obj.id,
                'subject_num' : sub_obj.subject_num,
                'subject_name' : sub_obj.subject_name,
                'parent' : sub_obj.parent.id if sub_obj.parent else '',
                'subject_type' : sub_obj.subject_type,
                'balance_type' : sub_obj.balance_type,
                'assists' : sub_obj.assist_list(),
                'num' : sub_obj.subjectofaccounts.num if hasattr(sub_obj, 'subjectofaccounts') else 0,
                'money' : sub_obj.subjectofaccounts.money if hasattr(sub_obj, 'subjectofaccounts') else 0,
                'assists' : sub_obj.assist_list()
            }
            data = {
                'sub_info': sub_info,
                'ass_list': ass_list,
                'all_subjects': all_subjects
            }
            return common_response(data=data)

        if data_type == 'info':
            data = {
                'all_subjects': all_subjects,
                'ass_list': ass_list
            }
            return common_response(data=data)

        if data_type == 'list':
            return common_response(data=all_subjects)


class AssisView(APIView):
    ''' 辅助核算管理 '''
    def post(self, request):
        # 验证用户信息
        is_log, user_id = is_logined(request)
        try:
            obj = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return common_response(code=500, msg='用户不存在!')

        # 验证用户权限
        if not has_permission(obj, 'Assis', 'POST'):
            return common_response(code=500, msg='您没有操作权限')

        data = request.data
        ass_name = data['name'] if 'name' in data else ''
        ass_obj = Assist.objects.create(
            assist_name=ass_name,
            village=obj.village
        )
        ass_obj.save()
        return common_response(msg='True')

    def delete(self, request):
        # 验证用户信息
        is_log, user_id = is_logined(request)
        try:
            obj = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return common_response(code=500, msg='用户不存在!')

        # 验证用户权限
        if not has_permission(obj, 'Assis', 'DELETE'):
            return common_response(code=500, msg='您没有操作权限')

        data = request.data
        ass_id = data.get('ass_id', '')
        try:
            ass_obj = Assist.objects.get(id=ass_id)
        except Assist.DoesNotExist:
            return common_response(code=500, msg='ID不存在')

        ass_obj.delete()
        return common_response(code=200)

    def put(self, request):
        # 验证用户信息
        is_log, user_id = is_logined(request)
        try:
            obj = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return common_response(code=500, msg='用户不存在!')

        # 验证用户权限
        if not has_permission(obj, 'Assis', 'PUT'):
            return common_response(code=500, msg='您没有操作权限')

        data = request.data
        ass_id = data['ass_id'] if 'ass_id' in data else ''
        ass_name = data['ass_name'] if 'ass_name' in data else ''
        try:
            ass_obj = Assist.objects.get(id=ass_id)
        except Assist.DoesNotExist:
            return common_response(code=500, msg='ID不存在')
        
        ass_obj.assist_name = ass_name
        ass_obj.save()
        return common_response(code=200)

    def get(self, request):
        # 获取所有的辅助核算
        # 验证用户信息
        is_log, user_id = is_logined(request)
        try:
            obj = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return common_response(code=500, msg='用户不存在!')

        # 验证用户权限
        if not has_permission(obj, 'Assis', 'GET'):
            return common_response(code=500, msg='您没有操作权限')

        # 详情
        ass_id = request.GET.get('ass_id', '')
        if ass_id:
            try:
                ass_obj = Assist.objects.get(id=ass_id)
            except Assist.DoesNotExist:
                return common_response(code=500, msg='id不存在') 
            else:
                info = {
                    'id': a_obj.id,
                    'name': ass_obj.assist_name
                }
                return common_response(data=info)

        # 辅助核算列表
        ass_obj = Assist.objects.all(village=obj.village)
        ass_list = []
        for a_obj in ass_obj:
            ass_info = {
                'id': a_obj.id,
                'name': a_obj.assist_name
            }
            ass_list.append(ass_info)

        return common_response(data=ass_list)


class BalanceView(APIView):
    def get(self, request):
        # 验证用户信息
        is_log, user_id = is_logined(request)
        try:
            obj = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return common_response(code=500, msg='用户不存在!')

        soa_id = request.GET.get('soa_id', '')
        if not soa_id:
            return common_response(code=500, msg='缺少帐套id')
        try:
            soa_obj = SetOfAccounts.objects.get(id=soa_id)
        except SetOfAccounts.DoesNotExist:
            return common_response(code=500, msg='帐套id不存在')
        
        # 帐套下所有的科目
        debtor_money = 0 # 借方金额
        credit_money = 0 # 贷方金额
        for sub_obj in soa_obj.accountofsubjects.all():
            if sub_obj.subject.balance_type == 0:
                debtor_money += sub_obj.num * sub_obj.money
            else:
                credit_money += sub_obj.num * sub_obj.money

        if debtor_money != credit_money:
            return common_response(msg='您录入的初始余额不平衡，请仔细核对')

        return common_response()


class SetSubjectMoneyView(APIView):
    def put(self, request):
        # 验证用户信息
        is_log, user_id = is_logined(request)
        try:
            obj = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return common_response(code=500, msg='用户不存在!')

        # 验证用户权限
        if not has_permission(obj, 'SetSubjectMoney', 'PUT'):
            return common_response(code=500, msg='您没有操作权限')

        # 验证帐套信息
        data = request.data
        soa_id = data.get('soa_id', 0)
        if not soa_id:
            return common_response(code=500, msg='缺少帐套id!')
        try:
            soa_obj = SetOfAccounts.objects.get(id=soa_id)
        except SetOfAccounts.DoesNotExist:
            return common_response(code=500, msg='帐套不存在!')

        subjects = json.loads(data['subjects'])
        for obj in subjects:
            try:
                subject_obj = Subject.objects.get(id=int(obj['id']))
            except Subject.DoesNotExist:
                continue

            num = obj.get('num', 0)
            money = Decimal(obj.get('money', 0)).quantize(Decimal('0.00'))
            balance = num * money
            if hasattr(subject_obj, 'subjectofaccounts'):
                subject_obj.subjectofaccounts.num = num
                subject_obj.subjectofaccounts.money = money
                subject_obj.subjectofaccounts.balance = balance
                subject_obj.subjectofaccounts.save()
                continue
            else:
                soa_obj = SubjectOfAccounts.objects.create(
                    account=soa_obj,
                    subject=subject_obj,
                    num=num,
                    money=money,
                    balance=balance
                )
                soa_obj.save()

        return common_response(msg='True')

    def get(self, request):
        # 验证用户信息
        is_log, user_id = is_logined(request)
        try:
            obj = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return common_response(code=500, msg='用户不存在!')

        # 验证用户权限
        if not has_permission(obj, 'SetSubjectMoney', 'GET'):
            return common_response(code=500, msg='您没有操作权限')

        # 验证帐套信息
        soa_id = request.GET.get('soa_id', 0)
        if not soa_id:
            return common_response(code=500, msg='缺少帐套id!')
        try:
            soa_obj = SetOfAccounts.objects.get(id=soa_id)
        except SetOfAccounts.DoesNotExist:
            return common_response(code=500, msg='帐套不存在!')

        # 获取所有科目
        all_subjects = get_all_subject(obj)
        
        return common_response(data=all_subjects)


    # def post(self, request):
    #     ''' 设置科目余额 '''
    #     # 验证用户信息
    #     is_log, user_id = is_logined(request)
    #     try:
    #         obj = User.objects.get(id=user_id)
    #     except User.DoesNotExist:
    #         return common_response(code=500, msg='用户不存在!')

    #     data = request.data
    #     soa_id = data.get('soa_id', 0)
    #     sub_data = data.get('sub_data', '')
    #     for child_data in sub_data:
    #         subject_id = data.get('subject_id', 0)
    #         num = data.get('num', 0)
    #         money = Decimal(data.get('money', 0)).quantize(Decimal('0.00'))
    #         if not soa_id or not subject_id:
    #             return common_response(code=500, msg='缺少帐套id')

    #         soa_obj = SubjectOfAccounts.objects.create(
    #             account_id=soa_id,
    #             subject_id=subject_id,
    #             num=num,
    #             money=money
    #         )
    #         soa_obj.save()
    #     return common_response(msg='True')

#     def put(self, request):
#         # 验证用户信息
#         is_log, user_id = is_logined(request)
#         try:
#             obj = User.objects.get(id=user_id)
#         except User.DoesNotExist:
#             return common_response(code=500, msg='用户不存在!')

#         data = request.data
#         update_id = data.get('update_id', 0)
#         soa_id = data.get('soa_id', 0)
#         subject_id = data.get('subject_id', 0)
#         num = data.get('num', 0)
#         money = Decimal(data.get('money', 0)).quantize(Decimal('0.00'))
#         if not soa_id or not subject_id or not update_id:
#             return common_response(code=500, msg='缺少帐套id')

#         try:
#             subofa_obj = SubjectOfAccounts.objects.get(id=update_id)
#         except SubjectOfAccounts.DoesNotExist:
#             return common_response(code=500, msg='id不存在')

#         subofa_obj.account_id = soa_id
#         subofa_obj.subject_id = subject_id
#         subofa_obj.num = num
#         subofa_obj.money = money
#         subofa_obj.save()
#         return common_response(msg='True')

