import json
from datetime import date, datetime
from rest_framework.views import APIView
from .models import *
from user.models import User
from user.func import is_logined
from subject.models import Subject, SubjectLog
from finance.basic import common_response
from utils.tools import HASHIDS
from decimal import Decimal


class VoucherView(APIView):
    ''' 凭证的增删改查 '''
    def post(self, request):
        # 接收数据并验证
        # 验证用户信息
        is_log, user_id = is_logined(request)
        try:
            user_obj = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return common_response(code=500, msg='用户不存在!')

        data = request.data
        voucher_word = data.get('voucher_word', '')
        soa_id = data.get('soa_id', '')
        voucher_type = data.get('voucher_type', 0)
        voucher_date = data.get('voucher_date', date.today())
        if isinstance(voucher_date, str):
            voucher_date = datetime.strptime(voucher_date, '%Y-%m-%d').date()
        subject_data = data.get('subjects', '')

        # 数据验证
        if not subject_data:
            return common_response(code=500, msg='科目信息不能为空')

        if not soa_id:
            return common_response(code=500, msg='帐套id不能为空')

        try:
            soa_obj = SetOfAccounts.objects.get(id=soa_id)
        except SetOfAccounts.DoesNotExist:
            return common_response(code=500, msg='帐套id不存在')

        # 验证借贷金额和摘要
        verification_debtor_money = 0
        verification_credit_money = 0
        subject_data = json.loads(subject_data)
        for sub in subject_data:
            verification_debtor_money += Decimal(sub.get('debtor_money', 0)).quantize(Decimal('0.00'))
            verification_credit_money += Decimal(sub.get('credit_money', 0)).quantize(Decimal('0.00'))
        if verification_debtor_money != verification_credit_money:
            return common_response(code=500, msg='录入借贷不平')

        if not subject_data[0]['abstract']:
            return common_response(code=500, msg='第一1条分录摘要不能为空！')

        voucher_obj = Voucher.objects.create(
            voucher_word=voucher_word,
            voucher_type=voucher_type,
            created_user=user_obj,
            voucher_date=voucher_date,
            soa=soa_obj
        )
        # 将科目加入
        for sub in subject_data:
            try:
                sub_obj = Subject.objects.get(id=sub['subject'])
            except Subject.DoesNotExist:
                return common_response(code=500, msg='科目id不存在')

            vou_child_obj = VoucherChild.objects.create(
                voucher = voucher_obj,
                subject = sub_obj,
                abstract = sub.get('abstract', ''),
                debtor_money = Decimal(sub.get('debtor_money', 0)).quantize(Decimal('0.00')),
                credit_money = Decimal(sub.get('credit_money', 0)).quantize(Decimal('0.00'))
            )
            vou_child_obj.save()

        voucher_obj.save()
        return common_response(msg='True')

    def delete(self, request):
        # 验证用户信息
        is_log, user_id = is_logined(request)
        try:
            obj = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return common_response(code=500, msg='用户不存在!')

        data = request.data
        voucher_id = data.get('voucher_id', '')
        if not voucher_id:
            return common_response(code=500, msg='缺少必要参数')
        try:
            voucher_obj = Voucher.objects.get(id=voucher_id)
        except Voucher.DoesNotExist:
            return common_response(code=500, msg='ID不存在')
        voucher_obj.delete()
        return common_response(msg='True')

    def put(self, request):
        # 接收数据并验证
        # 验证用户信息
        is_log, user_id = is_logined(request)
        try:
            obj = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return common_response(code=500, msg='用户不存在!')

        data = request.data
        voucher_id = data.get('voucher_id', '')
        if not voucher_id:
            return common_response(code=500, msg='缺少凭证id')

        # 查询并修改
        try:
            voucher_obj = Voucher.objects.get(id=voucher_id)
        except Voucher.DoesNotExist:
            return common_response(code=500, msg='ID不存在')

        voucher_word = data.get('voucher_word', voucher_obj.voucher_word)
        voucher_type = data.get('voucher_type', voucher_obj.voucher_type)
        voucher_date = data.get('voucher_date', voucher_obj.voucher_date)
        subject_data = data.get('subjects', '')
        if isinstance(voucher_date, str):
            voucher_date = datetime.strptime(voucher_date, '%Y-%m-%d').date()

        voucher_obj.voucher_word = voucher_word
        voucher_obj.voucher_type = voucher_type
        voucher_obj.voucher_date = voucher_date
        # 验证科目信息
        if subject_data:
            verification_debtor_money = 0
            verification_credit_money = 0
            subject_data = json.loads(subject_data)
            for sub in subject_data:
                verification_debtor_money += Decimal(sub.get('debtor_money', 0)).quantize(Decimal('0.00'))
                verification_credit_money += Decimal(sub.get('credit_money', 0)).quantize(Decimal('0.00'))
            if verification_debtor_money != verification_credit_money:
                return common_response(code=500, msg='录入借贷不平')

            if not subject_data[0]['abstract']:
                return common_response(code=500, msg='第一1条分录摘要不能为空！')

            # 修改相关科目信息
            voucher_obj.vouchilds.all().delete()
            for sub in subject_data:
                try:
                    sub_obj = Subject.objects.get(id=sub['subject'])
                except Subject.DoesNotExist:
                    return common_response(code=500, msg='科目id不存在')

                vou_child_obj = VoucherChild.objects.create(
                    abstract = sub.get('abstract', ''),
                    voucher = voucher_obj,
                    subject = sub_obj,
                    debtor_money = Decimal(sub.get('debtor_money', 0)).quantize(Decimal('0.00')),
                    credit_money = Decimal(sub.get('credit_money', 0)).quantize(Decimal('0.00'))
                )
                vou_child_obj.save()

        voucher_obj.save()
        return common_response(msg='True')

    def get(self, request):
        '''
            该方法用来获取凭证的相关信息
            如果get接收到voucher_id则获取当前凭证的所有信息 voucher_id的权限大于type
            通过type的值来区分获取什么值
            type == list 获取凭证列表
            type == info 获取凭证管理表的信息(主要用于修改和添加)
        '''
        # 验证用户信息
        is_log, user_id = is_logined(request)
        try:
            obj = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return common_response(code=500, msg='用户不存在!')

        voucher_id = request.GET.get('voucher_id', '')
        data_type = request.GET.get('type', 'info')
        sub_list = []
        if voucher_id or data_type == 'info':
            # 获取所有科目
            all_sub = Subject.objects.all()
            for sub_obj in all_sub:
                sub_info = {
                    'subject_id': sub_obj.id,
                    'subject_name': sub_obj.subject_name
                }
                sub_list.append(sub_info)

        if voucher_id:
            try:
                voucher_obj = Voucher.objects.get(id=voucher_id)
            except Voucher.DoesNotExist:
                return common_response(code=500, msg='凭证id不存在')
            else:
                # 获取子凭证
                child_vou_list = []
                for child_vou in voucher_obj.vouchilds.all():
                    child_info = {
                        'abstract': child_vou.abstract,
                        'subject': f'{child_vou.subject.subject_num} {child_vou.subject.subject_name}',
                        'debtor_money': child_vou.debtor_money,
                        'credit_money': child_vou.credit_money
                    }
                    child_vou_list.append(child_info)

            result = {
                'sub_list': sub_list,
                'voucher_info':{
                    'voucher_type': voucher_obj.voucher_type,
                    'voucher_date': datetime.strftime(voucher_obj.voucher_date,'%Y-%m-%d'),
                    'is_audit': voucher_obj.is_audit,
                    'subjects': child_vou_list
                }
            }

            return common_response(data=result)

        if data_type == 'info':
            return common_response(data=sub_list)

        if data_type == 'list':
            # 获取所有的凭证
            soa_id = request.GET.get('soa_id', '')
            if not soa_id:
                return common_response(code=500, msg='帐套id不能为空')

            try:
                soa_obj = SetOfAccounts.objects.get(id=soa_id)
            except SetOfAccounts.DoesNotExist:
                return common_response(code=500, msg='帐套id不存在')

            all_vouchers = Voucher.objects.filter(soa=soa_obj.id).all()
            voucher_list = []
            for voucher_obj in all_vouchers:
                voucher_info = {
                    'voucher_id': voucher_obj.id,
                    'voucher_word': voucher_obj.voucher_word,
                    'voucher_type': voucher_obj.get_voucher_type_display(),
                    'created_user': voucher_obj.created_user.username,
                    'check_user': voucher_obj.check_user.username if voucher_obj.check_user else '',
                    'voucher_date': datetime.strftime(voucher_obj.voucher_date,'%Y-%m-%d'),
                    'is_audit': voucher_obj.is_audit,
                    'child_vou': []
                }
                for vou_child_obj in voucher_obj.vouchilds.all():
                    child_info = {
                        'abstract': vou_child_obj.abstract,
                        'subject': f'{vou_child_obj.subject.subject_num} {vou_child_obj.subject.subject_name}',
                        'debtor_money': vou_child_obj.debtor_money,
                        'credit_money': vou_child_obj.credit_money
                    }
                    voucher_info['child_vou'].append(child_info)
                voucher_list.append(voucher_info)

            return common_response(data=voucher_list)


class VoucherCheckView(APIView):
    def get(self, request):
        ''' 凭证审核 '''
        # 验证用户信息
        is_log, user_id = is_logined(request)
        try:
            obj = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return common_response(code=500, msg='用户不存在!')

        voucher_id = request.GET.get('voucher_id', '')
        if not voucher_id:
            return common_response(code=500, msg='缺少凭证id')

        try:
            voucher_obj = Voucher.objects.get(id=voucher_id)
        except Voucher.DoesNotExist:
            return common_response(code=500, msg='凭证ID不存在')

        voucher_obj.is_audit = True
        voucher_obj.check_user = 1
        voucher_obj.save()
        return common_response(msg='True')

