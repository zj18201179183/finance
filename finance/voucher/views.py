import json
from datetime import date, datetime
from rest_framework.views import APIView
from .models import *
from user.models import User
from user.func import is_logined, has_permission
from subject.models import Subject
from subject.func import get_all_subject
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

        # 验证用户权限
        if not has_permission(user_obj, 'Voucher', 'POST'):
            return common_response(code=500, msg='您没有操作权限')

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

            # 借贷金额
            debtor_money = Decimal(sub.get('debtor_money', 0)).quantize(Decimal('0.00'))
            credit_money = Decimal(sub.get('credit_money', 0)).quantize(Decimal('0.00'))

            # 计算科目余额
            subjectofaccounts_obj = sub_obj.subjectofaccounts.filter(account=soa_obj).first()
            balance = subjectofaccounts_obj.balance
            if sub_obj.balance_type == 0:
                # 借 贷=减 借=加
                balance += debtor_money
                balance -= credit_money
            else:
                # 贷
                balance -= debtor_money
                balance += credit_money
            subjectofaccounts_obj.balance = balance
            subjectofaccounts_obj.save()

            vou_child_obj = VoucherChild.objects.create(
                voucher = voucher_obj,
                subject = sub_obj,
                abstract = sub.get('abstract', ''),
                debtor_money = debtor_money,
                credit_money = credit_money,
                balance=balance,
                add_date=voucher_date
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

        # 验证用户权限
        if not has_permission(obj, 'Voucher', 'DELETE'):
            return common_response(code=500, msg='您没有操作权限')

        data = request.data
        voucher_id = data.get('voucher_id', '')
        soa_id = data.get('soa_id', '')
        if not soa_id:
            return common_response(code=500, msg='帐套id不能为空')

        try:
            soa_obj = SetOfAccounts.objects.get(id=soa_id)
        except SetOfAccounts.DoesNotExist:
            return common_response(code=500, msg='帐套id不存在')

        if not voucher_id:
            return common_response(code=500, msg='缺少必要参数')
        try:
            voucher_obj = Voucher.objects.get(id=voucher_id)
        except Voucher.DoesNotExist:
            return common_response(code=500, msg='ID不存在')

        # 如果凭证已审核则不能删除
        if voucher_obj.is_audit:
            return common_response(code=500, msg='已审核的凭证不能删除')

        # 如果删除则将科目余额恢复
        for voucher_child_obj in voucher_obj.vouchilds.all():
            # 获取科目现在余额
            subjectofaccounts_obj = sub_obj.subjectofaccounts.filter(account=soa_obj).first()
            balance = subjectofaccounts_obj.balance
            if voucher_child_obj.subject.balance_type == 0:
                # 借 贷=减 借=加
                balance -= voucher_child_obj.debtor_money
                balance += voucher_child_obj.credit_money
            else:
                # 贷
                balance += voucher_child_obj.debtor_money
                balance -= voucher_child_obj.credit_money
            subjectofaccounts_obj.balance = balance
            subjectofaccounts_obj.save()

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

        # 验证用户权限
        if not has_permission(obj, 'Voucher', 'PUT'):
            return common_response(code=500, msg='您没有操作权限')

        data = request.data
        voucher_id = data.get('voucher_id', '')
        soa_id = data.get('soa_id', '')
        if not soa_id:
            return common_response(code=500, msg='帐套id不能为空')
        try:
            soa_obj = SetOfAccounts.objects.get(id=soa_id)
        except SetOfAccounts.DoesNotExist:
            return common_response(code=500, msg='帐套id不存在')

        if not voucher_id:
            return common_response(code=500, msg='缺少凭证id')

        # 查询并修改
        try:
            voucher_obj = Voucher.objects.get(id=voucher_id)
        except Voucher.DoesNotExist:
            return common_response(code=500, msg='ID不存在')

        # 如果凭证已审核则不能删除
        if voucher_obj.is_audit:
            return common_response(code=500, msg='已审核的凭证不能删除')

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
            # 验证借贷金额是否平衡
            verification_debtor_money = 0
            verification_credit_money = 0
            subject_data = json.loads(subject_data)
            for sub in subject_data:
                verification_debtor_money += Decimal(sub.get('debtor_money', 0)).quantize(Decimal('0.00'))
                verification_credit_money += Decimal(sub.get('credit_money', 0)).quantize(Decimal('0.00'))
            if verification_debtor_money != verification_credit_money:
                return common_response(code=500, msg='录入借贷不平')

            # 验证摘要
            if not subject_data[0]['abstract']:
                return common_response(code=500, msg='第一1条分录摘要不能为空！')

            # 先将科目的金额恢复
            voucher_child_all = voucher_obj.vouchilds.all()
            for voucher_child_obj in voucher_child_all:
                # 获取科目现在余额
                subjectofaccounts_obj = sub_obj.subjectofaccounts.filter(account=soa_obj).first()
                balance = subjectofaccounts_obj.balance
                if voucher_child_obj.subject.balance_type == 0:
                    # 借 贷=减 借=加
                    balance -= voucher_child_obj.debtor_money
                    balance += voucher_child_obj.credit_money
                else:
                    # 贷
                    balance += voucher_child_obj.debtor_money
                    balance -= voucher_child_obj.credit_money
                subjectofaccounts_obj.balance = balance
                subjectofaccounts_obj.save()
            voucher_child_all.delete()

            # 修改相关科目信息
            voucher_obj.vouchilds.all().delete()
            for sub in subject_data:
                try:
                    sub_obj = Subject.objects.get(id=sub['subject'])
                except Subject.DoesNotExist:
                    return common_response(code=500, msg='科目id不存在')

                # 借贷金额
                debtor_money = Decimal(sub.get('debtor_money', 0)).quantize(Decimal('0.00'))
                credit_money = Decimal(sub.get('credit_money', 0)).quantize(Decimal('0.00'))

                # 计算科目余额
                subjectofaccounts_obj = sub_obj.subjectofaccounts.filter(account=soa_obj).first()
                balance = subjectofaccounts_obj.balance
                if sub_obj.balance_type == 0:
                    # 借 贷=减 借=加
                    balance += debtor_money
                    balance -= credit_money
                else:
                    # 贷
                    balance -= debtor_money
                    balance += credit_money
                subjectofaccounts_obj.balance = balance
                subjectofaccounts_obj.save()

                vou_child_obj = VoucherChild.objects.create(
                    abstract = sub.get('abstract', ''),
                    voucher = voucher_obj,
                    subject = sub_obj,
                    debtor_money = debtor_money,
                    credit_money = credit_money,
                    balance=balance,
                    add_date = voucher_date
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

        # 验证用户权限
        if not has_permission(obj, 'Voucher', 'GET'):
            return common_response(code=500, msg='您没有操作权限')

        soa_id = request.GET.get('soa_id', '')
        voucher_id = request.GET.get('voucher_id', '')
        data_type = request.GET.get('type', 'info')
        if not soa_id:
            return common_response(code=500, msg='帐套id不能为空')

        # sub_list = {}
        # if voucher_id or data_type == 'info':
        #     # 获取所有科目
        #     sub_list = get_all_subject(obj)

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

            # result = {
            #     # 'sub_list': sub_list,
            #     'voucher_info':{
            #         'voucher_type': voucher_obj.voucher_type,
            #         'voucher_date': datetime.strftime(voucher_obj.voucher_date,'%Y-%m-%d'),
            #         'is_audit': voucher_obj.is_audit,
            #         'subjects': child_vou_list
            #     }
            # }
            voucher_info = {
                'voucher_type': voucher_obj.voucher_type,
                'voucher_date': datetime.strftime(voucher_obj.voucher_date,'%Y-%m-%d'),
                'is_audit': voucher_obj.is_audit,
                'subjects': child_vou_list
            }

            return common_response(data=voucher_info)

        if data_type == 'info':
            vou_obj = Voucher.objects.filter().order_by('-voucher_word').first()
            voucher_word = vou_obj.voucher_word+1 if vou_obj else 1
            data = {
                'voucher_word': voucher_word,
                # 'sub_list': sub_list
            }
            return common_response(data=data)

        if data_type == 'list':
            # 获取所有的凭证
            try:
                soa_obj = SetOfAccounts.objects.get(id=soa_id)
            except SetOfAccounts.DoesNotExist:
                return common_response(code=500, msg='帐套id不存在')

            all_vouchers = Voucher.objects.filter(soa=soa_obj.id).all()
            voucher_list = []
            for voucher_obj in all_vouchers:
                voucher_info = {
                    'voucher_id': voucher_obj.id,
                    'voucher_word': f"{voucher_obj.get_voucher_type_display()}-{voucher_obj.voucher_word}",
                    'created_user': voucher_obj.created_user.username,
                    'check_user': voucher_obj.check_user.username if voucher_obj.check_user else '未审核',
                    'voucher_date': datetime.strftime(voucher_obj.voucher_date,'%Y-%m-%d'),
                    'is_audit': voucher_obj.is_audit,
                    'child_vou': []
                }
                for vou_child_obj in voucher_obj.vouchilds.all():
                    child_info = {
                        'abstract': vou_child_obj.abstract,
                        'subject': f'{vou_child_obj.subject.subject_num} {vou_child_obj.subject.subject_name}',
                        'debtor_money': vou_child_obj.debtor_money if vou_child_obj.debtor_money else 0,
                        'credit_money': vou_child_obj.credit_money if vou_child_obj.credit_money else 0
                    }
                    voucher_info['child_vou'].append(child_info)
                voucher_list.append(voucher_info)

            return common_response(data=voucher_list)


class VoucherCheckView(APIView):
    def put(self, request):
        ''' 凭证审核 '''
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

        try:
            voucher_obj = Voucher.objects.get(id=voucher_id)
        except Voucher.DoesNotExist:
            return common_response(code=500, msg='凭证ID不存在')

        voucher_obj.is_audit = True
        voucher_obj.check_user = obj
        voucher_obj.save()
        return common_response(msg='True')


class TransferView(APIView):
    def get(self, request):
        ''' 结转损益 '''
        # 验证用户信息
        is_log, user_id = is_logined(request)
        try:
            user_obj = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return common_response(code=500, msg='用户不存在!')

        soa_id = request.GET.get('soa_id', '')
        if not soa_id:
            return common_response(code=500, msg='缺少帐套id')
        try:
            soa_obj = SetOfAccounts.objects.get(id=soa_id)
        except SetOfAccounts.DoesNotExist:
            return common_response(code=500, msg='帐套id不存在')

        # 计算本期日期
        start_date = soa_obj.date
        end_date = date(start_date.year+1, 1, 1)

        # 如果该帐套当期已经有结转损益凭证则删除重新生成
        Voucher.objects.filter(soa=soa_obj, is_pal=True, voucher_date__gte=start_date, voucher_date__lt=end_date).delete()

        # 获取凭证字号
        voucher_number = Voucher.objects.filter(soa=soa_obj, voucher_date__gte=start_date, voucher_date__lt=end_date).order_by('-voucher_word').first()
        number = voucher_number.voucher_word+1 if voucher_number else 1

        # 查找所有损益子凭证(如果没有直接返回)
        loss_child_voucher = VoucherChild.objects.filter(voucher__soa=soa_obj, add_date__gte=start_date, add_date__lt=end_date, subject__subject_type=4)
        if not loss_child_voucher:
            return common_response(msg='True')

        # 重新生结转本期损益
        voucher_obj = Voucher.objects.create(
            voucher_word=number,
            voucher_type=0,
            created_user=user_obj,
            voucher_date=date(start_date.year, 12, 31),
            soa=soa_obj,
            is_pal=True
        )
        number += 1
        debtor_money_amount = 0
        credit_money_amount = 0
        # 创建子凭证
        for obj in loss_child_voucher:
            vou_child_obj = VoucherChild.objects.create(
                abstract = '结转本期损益',
                voucher = voucher_obj,
                subject = obj.subject,
                debtor_money = obj.debtor_money,
                credit_money = obj.credit_money,
                balance=0,
                add_date = date.today()
            )
            if obj.subject.balance_type == 0:
                # 借 贷=减 借=加
                debtor_money_amount += obj.debtor_money
                credit_money_amount -= obj.credit_money
            else:
                # 贷
                debtor_money_amount -= obj.debtor_money
                credit_money_amount += obj.credit_money

        # 获取收益科目对象
        profit_subject_obj = Subject.objects.get(subject_num=321)
        # 本年收益总和(如果借方贷方金额相同则不统计)
        if debtor_money_amount != credit_money_amount:
            vou_child_obj = VoucherChild.objects.create(
                abstract = '结转本期损益',
                voucher = voucher_obj,
                subject = profit_subject_obj,
                debtor_money = debtor_money_amount,
                credit_money = credit_money_amount,
                balance=0,
                add_date = date.today()
            ) 
        vou_child_obj.save()
        voucher_obj.save()


        # 新建凭证 结转本年利润
        voucher_year_obj = Voucher.objects.create(
            voucher_word=number,
            voucher_type=0,
            created_user=user_obj,
            voucher_date=date(start_date.year, 12, 31),
            soa=soa_obj,
            is_pal=True
        )
        vou_year_child_obj = VoucherChild.objects.create(
            abstract = '结转本年利润',
            voucher = voucher_year_obj,
            subject = profit_subject_obj,
            debtor_money = debtor_money_amount,
            credit_money = credit_money_amount,
            balance=0,
            add_date = date.today()
        )
        voucher_year_obj.save()
        vou_year_child_obj.save()

        return common_response(msg='True')
