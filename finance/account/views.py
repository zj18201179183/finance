from datetime import date, datetime
from rest_framework.views import APIView
from django.db.models import Count, Sum
from .models import *
from user.models import User
from user.func import is_logined
from subject.models import Subject, SetOfAccounts, SubjectOfAccounts, Assist
from voucher.models import Voucher, VoucherChild
from finance.basic import common_response
from utils.tools import HASHIDS
from decimal import Decimal


class AccountDetailView(APIView):
    ''' 明细账表 '''
    def get(self, request):
        ''' 获取所有的凭证 '''
        # 验证用户信息
        is_log, user_id = is_logined(request)
        try:
            obj = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return common_response(code=500, msg='用户不存在!')

        # 默认第一期
        start_date = request.GET.get('date', date(date.today().year, 1, 1))
        if isinstance(start_date, str):
            date_list = start_date.split('-')
            start_date = date(int(date_list[0]), int(date_list[1]), 1)
        
        if start_date.month < 12:
            end_date = date(start_date.year, start_date.month+1, 1)
        else:
            end_date = date(start_date.year+1, 1, 1)

        soa_id = request.GET.get('soa_id', '')
        if not soa_id:
            return common_response(code=500, msg='缺少帐套id')

        voucher_obj = VoucherChild.objects.filter(voucher__voucher_date__gte=start_date, voucher__voucher_date__lt=end_date, voucher__soa=soa_id)
        # 如果没有数据直接返回空
        if not voucher_obj:
            return common_response()

        # 处理数据
        result = {}
        balance = {}
        for key, obj in enumerate(voucher_obj):
            if not obj.subject.subject_name in result:
                result[obj.subject.subject_name] = []
                balance[obj.subject.subject_name] = {
                    'balance': 0,
                    'all_debtor_money': 0,
                    'all_credit_money': 0
                }

            # 计算余额
            if key == 0:
                soa_obj = obj.subject.subjectofaccountss.filter(account=soa_id)[0]
                balance[obj.subject.subject_name]['balance'] = soa_obj.num * soa_obj.money
                voucher_info = {
                    'date': datetime.strftime(obj.voucher.voucher_date,'%Y-%m-%d'),
                    'voucher_word': '',
                    'abstract': '初期余额',
                    'debtor_money': '',
                    'credit_money': '',
                    'subject_type': obj.subject.get_balance_type_display(),
                    'balance': balance[obj.subject.subject_name]['balance']
                }

            else:
                if obj.subject.balance_type == 0:
                    balance[obj.subject.subject_name]['balance'] += obj.debtor_money
                    balance[obj.subject.subject_name]['balance'] += obj.credit_money
                else:
                    balance[obj.subject.subject_name]['balance'] -= obj.debtor_money
                    balance[obj.subject.subject_name]['balance'] -= obj.credit_money

                balance[obj.subject.subject_name]['all_debtor_money'] += obj.debtor_money
                balance[obj.subject.subject_name]['all_credit_money'] += obj.credit_money

                voucher_info = {
                    'date': datetime.strftime(obj.voucher.voucher_date,'%Y-%m-%d'),
                    'voucher_word': f'{obj.voucher.get_voucher_type_display()}-{obj.voucher.voucher_word}',
                    'abstract': obj.abstract,
                    'debtor_money': obj.debtor_money,
                    'credit_money': obj.credit_money,
                    'subject_type': obj.subject.get_balance_type_display(),
                    'balance': balance[obj.subject.subject_name]['balance']
                }
            result[obj.subject.subject_name].append(voucher_info)
        for key, val in balance.items():
            voucher_info = {
                'date': start_date,
                'voucher_word': '',
                'abstract': '本期合计',
                'debtor_money': val['all_debtor_money'],
                'credit_money': val['all_credit_money'],
                'subject_type': '',
                'balance': val['balance']
            }
            result[key].append(voucher_info)
        return common_response(data=result)


class AllAccountView(APIView):
    def get(self, request):
        # 验证用户信息
        is_log, user_id = is_logined(request)
        try:
            obj = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return common_response(code=500, msg='用户不存在!')

        soa_id = request.GET.get('soa_id', '') # 帐套id
        if not soa_id:
            return common_response(code=500, msg='缺少帐套id')

        try:
            soa_obj = SetOfAccounts.objects.get(id=soa_id)
        except SetOfAccounts.DoesNotExist:
            return common_response(code=500, msg='帐套id不存在')

        # 获取年初日期
        initial_start_date = date(soa_obj.date.year, 1, 1) 
        initial_end_date = date(soa_obj.date.year, 2, 1) 

        # 获取本期日期
        start_date = date(soa_obj.date.year, date.today().month, 1)
        end_date = date(soa_obj.date.year, date.today().month+1, 1)

        # 本年日期
        final_start_date = date(soa_obj.date.year, 1, 1)
        final_end_date = date(soa_obj.date.year+1, 1, 1)

        result = {}
        # 先计算年初余额
        initial_voucher_obj = VoucherChild.objects.filter(voucher__voucher_date__gte=initial_start_date, voucher__voucher_date__lt=initial_end_date, voucher__soa=soa_id).values('subject').annotate(debtor_amount=Sum('debtor_money'), credit_amount=Sum('credit_money')).values('subject', 'subject__subject_name', 'debtor_amount', 'credit_amount')
        for initial_obj in initial_voucher_obj:
            if initial_obj['subject'] not in result:
                result[initial_obj['subject']] = {
                    'subject_name': initial_obj['subject__subject_name'],
                    'initial_date': datetime.strftime(initial_start_date,'%Y-%m-%d'),
                    'initial_abstract': '年初余额',
                    'initial_debtor_amount': Decimal(0).quantize(Decimal('0.00')),
                    'initial_credit_amount': Decimal(0).quantize(Decimal('0.00')),
                    'initial_balance': Decimal(0).quantize(Decimal('0.00')),
                    'date': datetime.strftime(start_date,'%Y-%m-%d'),
                    'abstract': '本期合计',
                    'debtor_amount': Decimal(0).quantize(Decimal('0.00')),
                    'credit_amount': Decimal(0).quantize(Decimal('0.00')),
                    'balance': Decimal(0).quantize(Decimal('0.00')),
                    'final_date': datetime.strftime(final_start_date,'%Y-%m-%d'),
                    'final_abstract': '本年累计',
                    'final_debtor_amount': Decimal(0).quantize(Decimal('0.00')),
                    'final_credit_amount': Decimal(0).quantize(Decimal('0.00')),
                    'final_balance': Decimal(0).quantize(Decimal('0.00')),
                }
            result[initial_obj['subject']]['initial_debtor_amount'] += initial_obj['debtor_amount']
            result[initial_obj['subject']]['initial_credit_amount'] += initial_obj['debtor_amount']

        # 计算当期余额
        voucher_obj = VoucherChild.objects.filter(voucher__voucher_date__gte=start_date, voucher__voucher_date__lt=end_date, voucher__soa=soa_id).values('subject').annotate(debtor_amount=Sum('debtor_money'), credit_amount=Sum('credit_money')).values('subject', 'subject__subject_name', 'debtor_amount', 'credit_amount')
        for obj in voucher_obj:
            if obj['subject'] not in result:
                result[obj['subject']] = {
                    'subject_name': obj['subject__subject_name'],
                    'initial_date': datetime.strftime(initial_start_date,'%Y-%m-%d'),
                    'initial_abstract': '年初余额',
                    'initial_debtor_amount': Decimal(0).quantize(Decimal('0.00')),
                    'initial_credit_amount': Decimal(0).quantize(Decimal('0.00')),
                    'initial_balance': Decimal(0).quantize(Decimal('0.00')),
                    'date': datetime.strftime(start_date,'%Y-%m-%d'),
                    'abstract': '本期合计',
                    'debtor_amount': Decimal(0).quantize(Decimal('0.00')),
                    'credit_amount': Decimal(0).quantize(Decimal('0.00')),
                    'balance': Decimal(0).quantize(Decimal('0.00')),
                    'final_date': datetime.strftime(final_start_date,'%Y-%m-%d'),
                    'final_abstract': '本年累计',
                    'final_debtor_amount': Decimal(0).quantize(Decimal('0.00')),
                    'final_credit_amount': Decimal(0).quantize(Decimal('0.00')),
                    'final_balance': Decimal(0).quantize(Decimal('0.00')),
                }
            result[obj['subject']]['debtor_amount'] += obj['debtor_amount']
            result[obj['subject']]['credit_amount'] += obj['debtor_amount']


        # 计算年末余额
        final_voucher_obj = VoucherChild.objects.filter(voucher__voucher_date__gte=final_start_date, voucher__voucher_date__lt=final_end_date, voucher__soa=soa_id).values('subject').annotate(debtor_amount=Sum('debtor_money'), credit_amount=Sum('credit_money')).values('subject', 'subject__subject_name', 'debtor_amount', 'credit_amount')
        for final_obj in final_voucher_obj:
            if final_obj['subject'] not in result:
                result[final_obj['subject']] = {
                    'subject_name': final_obj['subject__subject_name'],
                    'initial_date': datetime.strftime(initial_start_date,'%Y-%m-%d'),
                    'initial_abstract': '年初余额',
                    'initial_debtor_amount': Decimal(0).quantize(Decimal('0.00')),
                    'initial_credit_amount': Decimal(0).quantize(Decimal('0.00')),
                    'initial_balance': Decimal(0).quantize(Decimal('0.00')),
                    'date': datetime.strftime(start_date,'%Y-%m-%d'),
                    'abstract': '本期合计',
                    'debtor_amount': Decimal(0).quantize(Decimal('0.00')),
                    'credit_amount': Decimal(0).quantize(Decimal('0.00')),
                    'balance': Decimal(0).quantize(Decimal('0.00')),
                    'final_date': datetime.strftime(final_start_date,'%Y-%m-%d'),
                    'final_abstract': '本年累计',
                    'final_debtor_amount': Decimal(0).quantize(Decimal('0.00')),
                    'final_credit_amount': Decimal(0).quantize(Decimal('0.00')),
                    'final_balance': Decimal(0).quantize(Decimal('0.00')),
                }
            result[final_obj['subject']]['final_debtor_amount'] += final_obj['debtor_amount']
            result[final_obj['subject']]['final_credit_amount'] += final_obj['credit_amount']

        for key, val in result.items():
            sub_obj = Subject.objects.get(id=key)
            soa_obj_all = sub_obj.subjectofaccountss.all()
            if not soa_obj_all:
                balance = 0
            else:
                soa_obj = soa_obj_all[0]
                balance = soa_obj.num * soa_obj.money

            result[key]['type'] = sub_obj.get_balance_type_display()
            result[key]['number'] = sub_obj.subject_num
            # 计算余额
            if sub_obj.balance_type == 0:
                balance = balance + val['initial_debtor_amount'] + val['initial_credit_amount']
                result[key]['initial_balance'] = balance
                balance = balance + val['debtor_amount'] + val['credit_amount']
                result[key]['balance'] = balance
                # balance = balance + val['final_debtor_amount'] + val['final_credit_amount']
                result[key]['final_balance'] = balance

            else:
                balance = balance - val['initial_debtor_amount'] - val['initial_credit_amount']
                result[key]['initial_balance'] = balance
                balance = balance - val['debtor_amount'] - val['credit_amount']
                result[key]['balance'] = balance
                # balance = balance - val['final_debtor_amount'] - val['final_credit_amount']
                result[key]['final_balance'] = balance

        return common_response(data=result)


# class SubjectAccountView(APIView):
#     def get(self, request):
#         # 默认第一期
#         start_date = request.GET.get('date', date(date.today().year, 1, 1))
#         if isinstance(start_date, str):
#             date_list = start_date.split('-')
#             start_date = date(int(date_list[0]), int(date_list[1]), 1)
        
#         # 本期发生额
#         if start_date.month < 12:
#             end_date = date(start_date.year, start_date.month+1, 1)
#         else:
#             end_date = date(start_date.year+1, 1, 1)
        

        # 本年发生额


class BusinessAccountView(APIView):
    def get(self, request):
        soa_id = request.GET.get('soa_id', '') # 帐套id
        business_id = request.GET.get('business_id', '') # 帐套id
        if not soa_id or not business_id:
            return common_response(code=500, msg='缺少必要id')

        try:
            soa_obj = SetOfAccounts.objects.get(id=soa_id)
        except SetOfAccounts.DoesNotExist:
            return common_response(code=500, msg='帐套id不存在')

        try:
            business_obj = Assist.objects.get(id=business_id)
        except Assist.DoesNotExist:
            return common_response(code=500, msg='辅助核算id不存在')

        # 获取年初日期
        initial_start_date = date(soa_obj.date.year, 1, 1) 
        initial_end_date = date(soa_obj.date.year, 2, 1) 

        # 获取本期日期
        start_date = date(soa_obj.date.year, date.today().month, 1)
        end_date = date(soa_obj.date.year, date.today().month+1, 1)

        # 本年日期
        final_start_date = date(soa_obj.date.year, 1, 1)
        final_end_date = date(soa_obj.date.year+1, 1, 1)

        result = {}
        # 获取辅助核算对应的科目余额
        for business_sub_ob in business_obj.assists.all():
            # 先计算年初余额
            initial_voucher_obj = VoucherChild.objects.filter(voucher__voucher_date__gte=initial_start_date, voucher__voucher_date__lt=initial_end_date, voucher__soa=soa_id, subject=business_sub_ob).values('subject').annotate(debtor_amount=Sum('debtor_money'), credit_amount=Sum('credit_money')).values('subject', 'subject__subject_name', 'debtor_amount', 'credit_amount')
            for initial_obj in initial_voucher_obj:
                if initial_obj['subject'] not in result:
                    result[initial_obj['subject']] = {
                        'subject_name': initial_obj['subject__subject_name'],
                        'initial_date': datetime.strftime(initial_start_date,'%Y-%m-%d'),
                        'initial_abstract': '年初余额',
                        'initial_debtor_amount': Decimal(0).quantize(Decimal('0.00')),
                        'initial_credit_amount': Decimal(0).quantize(Decimal('0.00')),
                        'initial_balance': Decimal(0).quantize(Decimal('0.00')),
                        'date': datetime.strftime(start_date,'%Y-%m-%d'),
                        'abstract': '本期合计',
                        'debtor_amount': Decimal(0).quantize(Decimal('0.00')),
                        'credit_amount': Decimal(0).quantize(Decimal('0.00')),
                        'balance': Decimal(0).quantize(Decimal('0.00')),
                        'final_date': datetime.strftime(final_start_date,'%Y-%m-%d'),
                        'final_abstract': '本年累计',
                        'final_debtor_amount': Decimal(0).quantize(Decimal('0.00')),
                        'final_credit_amount': Decimal(0).quantize(Decimal('0.00')),
                        'final_balance': Decimal(0).quantize(Decimal('0.00')),
                    }
                result[initial_obj['subject']]['initial_debtor_amount'] += initial_obj['debtor_amount']
                result[initial_obj['subject']]['initial_credit_amount'] += initial_obj['debtor_amount']

            # 计算当期余额
            voucher_obj = VoucherChild.objects.filter(voucher__voucher_date__gte=start_date, voucher__voucher_date__lt=end_date, voucher__soa=soa_id).values('subject').annotate(debtor_amount=Sum('debtor_money'), credit_amount=Sum('credit_money')).values('subject', 'subject__subject_name', 'debtor_amount', 'credit_amount')
            for obj in voucher_obj:
                if obj['subject'] not in result:
                    result[obj['subject']] = {
                        'subject_name': obj['subject__subject_name'],
                        'initial_date': datetime.strftime(initial_start_date,'%Y-%m-%d'),
                        'initial_abstract': '年初余额',
                        'initial_debtor_amount': Decimal(0).quantize(Decimal('0.00')),
                        'initial_credit_amount': Decimal(0).quantize(Decimal('0.00')),
                        'initial_balance': Decimal(0).quantize(Decimal('0.00')),
                        'date': datetime.strftime(start_date,'%Y-%m-%d'),
                        'abstract': '本期合计',
                        'debtor_amount': Decimal(0).quantize(Decimal('0.00')),
                        'credit_amount': Decimal(0).quantize(Decimal('0.00')),
                        'balance': Decimal(0).quantize(Decimal('0.00')),
                        'final_date': datetime.strftime(final_start_date,'%Y-%m-%d'),
                        'final_abstract': '本年累计',
                        'final_debtor_amount': Decimal(0).quantize(Decimal('0.00')),
                        'final_credit_amount': Decimal(0).quantize(Decimal('0.00')),
                        'final_balance': Decimal(0).quantize(Decimal('0.00')),
                    }
                result[obj['subject']]['debtor_amount'] += obj['debtor_amount']
                result[obj['subject']]['credit_amount'] += obj['debtor_amount']


            # 计算年末余额
            final_voucher_obj = VoucherChild.objects.filter(voucher__voucher_date__gte=final_start_date, voucher__voucher_date__lt=final_end_date, voucher__soa=soa_id).values('subject').annotate(debtor_amount=Sum('debtor_money'), credit_amount=Sum('credit_money')).values('subject', 'subject__subject_name', 'debtor_amount', 'credit_amount')
            for final_obj in final_voucher_obj:
                if final_obj['subject'] not in result:
                    result[final_obj['subject']] = {
                        'subject_name': final_obj['subject__subject_name'],
                        'initial_date': datetime.strftime(initial_start_date,'%Y-%m-%d'),
                        'initial_abstract': '年初余额',
                        'initial_debtor_amount': Decimal(0).quantize(Decimal('0.00')),
                        'initial_credit_amount': Decimal(0).quantize(Decimal('0.00')),
                        'initial_balance': Decimal(0).quantize(Decimal('0.00')),
                        'date': datetime.strftime(start_date,'%Y-%m-%d'),
                        'abstract': '本期合计',
                        'debtor_amount': Decimal(0).quantize(Decimal('0.00')),
                        'credit_amount': Decimal(0).quantize(Decimal('0.00')),
                        'balance': Decimal(0).quantize(Decimal('0.00')),
                        'final_date': datetime.strftime(final_start_date,'%Y-%m-%d'),
                        'final_abstract': '本年累计',
                        'final_debtor_amount': Decimal(0).quantize(Decimal('0.00')),
                        'final_credit_amount': Decimal(0).quantize(Decimal('0.00')),
                        'final_balance': Decimal(0).quantize(Decimal('0.00')),
                    }
                result[final_obj['subject']]['final_debtor_amount'] += final_obj['debtor_amount']
                result[final_obj['subject']]['final_credit_amount'] += final_obj['credit_amount']

            for key, val in result.items():
                sub_obj = Subject.objects.get(id=key)
                soa_obj_all = sub_obj.subjectofaccountss.all()
                if not soa_obj_all:
                    balance = 0
                else:
                    soa_obj = soa_obj_all[0]
                    balance = soa_obj.num * soa_obj.money

                result[key]['type'] = sub_obj.get_balance_type_display()
                result[key]['number'] = sub_obj.subject_num
                # 计算余额
                if sub_obj.balance_type == 0:
                    balance = balance + val['initial_debtor_amount'] + val['initial_credit_amount']
                    result[key]['initial_balance'] = balance
                    balance = balance + val['debtor_amount'] + val['credit_amount']
                    result[key]['balance'] = balance
                    # balance = balance + val['final_debtor_amount'] + val['final_credit_amount']
                    result[key]['final_balance'] = balance

                else:
                    balance = balance - val['initial_debtor_amount'] - val['initial_credit_amount']
                    result[key]['initial_balance'] = balance
                    balance = balance - val['debtor_amount'] - val['credit_amount']
                    result[key]['balance'] = balance
                    # balance = balance - val['final_debtor_amount'] - val['final_credit_amount']
                    result[key]['final_balance'] = balance

        return common_response(data=result)

