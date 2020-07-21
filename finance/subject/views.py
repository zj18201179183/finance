from decimal import Decimal
from datetime import date, datetime
from rest_framework.views import APIView
from .models import *
from finance.basic import common_response
from utils.tools import HASHIDS

# Create your views here.

class SetOfAccountsView(APIView):
    ''' 设置帐套 '''
    def post(self, request):
        data = request.data
        name = data.get('name', '')
        soa_date = data.get('date', date.today())
        if isinstance(soa_date, str):
            soa_date = datetime.strptime(soa_date, '%Y-%m-%d').date()
        if not name:
            return common_response(code=500, msg='帐套名不能为空')

        soa_obj = SetOfAccounts.objects.create(
            name=name,
            date=soa_date
        )
        soa_obj.save()
        return common_response(msg='True')

    # def delete(self, request):
    #     data = request.data
    #     sof_id = data.get('sof_id', 0)
    #     if not sof_id:
    #         return common_response(code=500, msg='缺少id')
        
    #     try:
    #         sof_obj = SetOfAccounts.objects.get(id=sof_id)
    #     except SetOfAccounts.DoesNotExist:
    #         return common_response(code=500, msg='ID不存在')
    #     sof_obj.delete()
    #     return common_response(msg='True')

    # def put(self, request):
    #     pass

    # def get(self, request):
    #     pass


class SubjectView(APIView):
    ''' 科目管理 '''
    def post(self, request):
        data = request.data
        # 验证数据
        subject_num = data.get('subject_num', '')
        subject_name = data.get('subject_name', '')
        subject_father = data.get('subject_father', None)
        subject_type =data.get('subject_type', 0)
        balance_type = data.get('balance_type', 0)
        assists = data.get('assists', 0)

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
            balance_type=balance_type
        )
        # 存储多对多关联表数据
        if assists:
            # 字符串转为列表
            ass_list = assists.strip(',').split(',')
            ass_obj = Assist.objects.filter(id__in=ass_list)
            subject_obj.assist_business.add(*ass_obj)
        subject_obj.save()
        return common_response(msg='succ')

    def delete(self, request):
        data = request.data
        sub_id = HASHIDS.decode(data['sub_id'])[0]
        try:
            sub_obj = Subject.objects.get(id=sub_id)
        except Subject.DoesNotExist:
            return common_response(code=500, msg='ID不存在')

        sub_obj.delete()
        return common_response(code=200)

    def put(self, request):
        data = request.data
        # 获取项目id
        sub_id = data.get('sub_id', 0)
        if not sub_id:
            return common_response(code=500, msg='没有接收到ID')
        try:
            sub_obj = Subject.objects.get(id=sub_id)
        except Subject.DoesNotExist:
            return common_response(code=500, msg='ID不存在')

        # 验证数据
        subject_num = data.get('subject_num', '')
        subject_name = data.get('subject_name', '')
        subject_father = data.get('subject_father', None)
        subject_type = data.get('subject_type', 0)
        balance_type = data.get('balance_type', 0)
        assists = data.get('assists', 0)

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

        sub_obj.subject_num = subject_num
        sub_obj.subject_name = subject_name
        sub_obj.parent = subject_father
        sub_obj.subject_type = subject_type
        sub_obj.balance_type = balance_type

        # 修改多对多关联表数据
        if assists:
            # 字符串转为列表
            ass_list = assists.strip(',').split(',')
            # ass_obj = Assist.objects.filter(id__in=ass_list)
            sub_obj.assist_business.clear()
            sub_obj.assist_business.set(ass_list)

        sub_obj.save()

        return common_response(msg='succ')

    def get(self, request):
        ''' 
            通过data_type来区分获取的数据 
                data_type为info获取相关数据(主要是获取辅助核算列表)
                data_type为list获取项目列表
            通过sub_id获取项目详情
            sub_id 优先级大雨data_type
        '''
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

        if sub_id:
            try:
                sub_obj = Subject.objects.get(id=sub_id)
            except Subject.DoesNotExist:
                return common_response(code=500, msg='项目id不存在')
            
            sub_info = {
                'subject_num' : sub_obj.subject_num,
                'subject_name' : sub_obj.subject_name,
                'parent' : sub_obj.parent.id,
                'subject_type' : sub_obj.subject_type,
                'balance_type' : sub_obj.balance_type,
                'assists' : sub_obj.assist_list()
            }
            data = {
                'sub_info': sub_info,
                'ass_list': ass_list
            }
            return common_response(data=data)

        if data_type == 'info':
            return common_response(data=ass_list)

        if data_type == 'list':
            sub_all = Subject.objects.all()
            sub_list = []
            for sub_obj in sub_all:
                sub_info = {
                    'subject_num': sub_obj.subject_num,
                    'subject_name': sub_obj.subject_name,
                    'parent': sub_obj.parent.subject_name if sub_obj.parent else '-',
                    'subject_type': sub_obj.get_subject_type_display(),
                    'balance_type': sub_obj.get_balance_type_display(),
                }
                sub_list.append(sub_info)
            return common_response(data=sub_list)


class AssisView(APIView):
    ''' 辅助核算管理 '''
    def post(self, request):
        data = request.data
        ass_name = data['name'] if 'name' in data else ''
        ass_obj = Assist.objects.create(assist_name=ass_name)
        ass_obj.save()
        return common_response(msg='True')

    def delete(self, request):
        data = request.data
        ass_id = HASHIDS.decode(data['ass_id'])[0]
        try:
            ass_obj = Assist.objects.get(id=ass_id)
        except Assist.DoesNotExist:
            return common_response(code=500, msg='ID不存在')

        ass_obj.delete()
        return common_response(code=200)

    def put(self, request):
        data = request.data
        ass_id = HASHIDS.decode(data['ass_id'])[0]
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
        ass_obj = Assist.objects.all()
        ass_list = []
        for obj in ass_obj:
            ass_info = {
                'id': HASHIDS.encode(obj.id),
                'name': obj.assist_name
            }
            ass_list.append(ass_info)

        return common_response(data=ass_list)


class SetSubjectMoneyView(APIView):
    def post(self, request):
        data = request.data
        soa_id = data.get('soa_id', 0)
        subject_id = data.get('subject_id', 0)
        num = data.get('num', 0)
        money = Decimal(data.get('money', 0)).quantize(Decimal('0.00'))
        if not soa_id or not subject_id:
            return common_response(code=500, msg='缺少id')

        soa_obj = SubjectOfAccounts.objects.create(
            account_id=soa_id,
            subject_id=subject_id,
            num=num,
            money=money
        )
        soa_obj.save()
        return common_response(msg='True')

    def put(self, request):
        data = request.data
        update_id = data.get('update_id', 0)
        soa_id = data.get('soa_id', 0)
        subject_id = data.get('subject_id', 0)
        num = data.get('num', 0)
        money = Decimal(data.get('money', 0)).quantize(Decimal('0.00'))
        if not soa_id or not subject_id or not update_id:
            return common_response(code=500, msg='缺少id')

        try:
            subofa_obj = SubjectOfAccounts.objects.get(id=update_id)
        except SubjectOfAccounts.DoesNotExist:
            return common_response(code=500, msg='id不存在')

        subofa_obj.account_id = soa_id
        subofa_obj.subject_id = subject_id
        subofa_obj.num = num
        subofa_obj.money = money
        subofa_obj.save()
        return common_response(msg='True')

