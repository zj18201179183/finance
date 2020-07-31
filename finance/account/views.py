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

        soa_id = request.GET.get('soa_id', '')
        if not soa_id:
            return common_response(code=500, msg='缺少帐套id')
        try:
            soa_obj = SetOfAccounts.objects.get(id=soa_id)
        except SetOfAccounts.DoesNotExist:
            return common_response(code=500, msg='帐套id不存在')

        # 默认当期
        start_date = request.GET.get('date', date(date.today().year, date.today().month, 1))
        if isinstance(start_date, str) and start_date != '':
            date_list = start_date.split('-')
            start_date = date(int(date_list[0]), int(date_list[1]), 1)
        if start_date.month < 12:
            end_date = date(start_date.year, start_date.month+1, 1)
        else:
            end_date = date(start_date.year+1, 1, 1)

        # 日期 科目 帐套 凭证
        result = {}
        voucher_child_obj = VoucherChild.objects.filter(add_date__gte=start_date, add_date__lt=end_date, voucher__is_pal=False) 
        for child_obj in voucher_child_obj:
            if child_obj.subject.subject_name not in result:
                # 初期余额
                setofaccounts_obj = child_obj.subject.subjectofaccounts.filter(account=soa_obj).first()
                begin_subject_info = {
                    'id': child_obj.subject.id,
                    'number': child_obj.subject.subject_num,
                    'subject_name': child_obj.subject.subject_name,
                    'info': [
                        {
                            'date': datetime.strftime(soa_obj.date, '%Y-%m-%d'),
                            'voucher_word': '',
                            'abstract': '年初余额',
                            'debtor_money': 0,
                            'credit_money': 0,
                            'type': child_obj.subject.get_balance_type_display(),
                            'balance': setofaccounts_obj.num*setofaccounts_obj.money,
                        }
                    ]
                }
                result[child_obj.subject.subject_name] = begin_subject_info

            now_voucher_info = {
                'date': datetime.strftime(child_obj.add_date, '%Y-%m-%d'),
                'voucher_word': f'{child_obj.voucher.get_voucher_type_display()}-{child_obj.voucher.voucher_word}',
                'abstract': child_obj.abstract,
                'debtor_money': child_obj.debtor_money,
                'credit_money': child_obj.credit_money,
                'type': child_obj.subject.get_balance_type_display(),
                'balance': child_obj.balance
            }
            result[child_obj.subject.subject_name]['info'].append(now_voucher_info)

        # 计算本期本年账表
        for key, val in result.items():
            # 本期账单
            now_obj = voucher_child_obj.filter(subject__id=val['id']).values('subject__id').annotate(debtor_amount=Sum('debtor_money'), credit_amount=Sum('credit_money')).values('subject', 'subject__subject_name', 'debtor_amount', 'credit_amount')
            new_voucher_child_obj = VoucherChild.objects.filter(subject__id=val['id'], add_date__gte=start_date, add_date__lt=end_date).order_by('-created_at').first()
            now_info = {
                "date": datetime.strftime(start_date, '%Y-%m-%d'),
                "voucher_word": "",
                "abstract": "本期合计",
                "debtor_money": now_obj[0]['debtor_amount'],
                "credit_money": now_obj[0]['credit_amount'],
                "type": new_voucher_child_obj.subject.get_balance_type_display(),
                "balance": new_voucher_child_obj.balance
            }
            # 本年账单
            year_start_date = date(soa_obj.date.year, 1, 1)
            year_end_date = date(soa_obj.date.year+1, 1, 1)

            year_obj = VoucherChild.objects.filter(add_date__gte=year_start_date, add_date__lt=year_end_date, subject__id=val['id']).values('subject__id').annotate(debtor_amount=Sum('debtor_money'), credit_amount=Sum('credit_money')).values('subject', 'subject__subject_name', 'debtor_amount', 'credit_amount')
            year_voucher_child_obj = VoucherChild.objects.filter(subject__id=val['id'], add_date__gte=year_start_date, add_date__lt=year_end_date).order_by('-created_at').first()
            year_info = {
                "date": datetime.strftime(start_date, '%Y-%m-%d'),
                "voucher_word": "",
                "abstract": "本年累计",
                "debtor_money": year_obj[0]['debtor_amount'],
                "credit_money": year_obj[0]['credit_amount'],
                "type": year_voucher_child_obj.subject.get_balance_type_display(),
                "balance": year_voucher_child_obj.balance
            }
            result[key]['info'].append(now_info)
            result[key]['info'].append(year_info)
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

        # 获取本期日期
        start_date = request.GET.get('date', date(date.today().year, date.today().month, 1))
        if isinstance(start_date, str) and start_date != '':
            date_list = start_date.split('-')
            start_date = date(int(date_list[0]), int(date_list[1]), 1)
        if start_date.month < 12:
            end_date = date(start_date.year, start_date.month+1, 1)
        else:
            end_date = date(start_date.year+1, 1, 1)

        # 本年日期
        final_start_date = date(soa_obj.date.year, 1, 1)
        final_end_date = date(soa_obj.date.year+1, 1, 1)

        result = []
        year_soa_obj = SubjectOfAccounts.objects.filter(account=soa_obj, created_at__gte=final_start_date, created_at__lt=final_end_date)
        for obj in year_soa_obj:
            year_obj = VoucherChild.objects.filter(voucher__is_pal=False, add_date__gte=final_start_date, add_date__lt=final_end_date, subject=obj.subject).values('subject').annotate(debtor_amount=Sum('debtor_money'), credit_amount=Sum('credit_money')).values('subject', 'debtor_amount', 'credit_amount')
            now_obj = VoucherChild.objects.filter(voucher__is_pal=False, add_date__gte=start_date, add_date__lt=end_date, subject=obj.subject).values('subject').annotate(debtor_amount=Sum('debtor_money'), credit_amount=Sum('credit_money')).values('subject', 'debtor_amount', 'credit_amount')
            new_voucher_child_obj = VoucherChild.objects.filter(voucher__is_pal=False, subject=obj.subject, add_date__lt=end_date).order_by('-created_at').first()
            info = {
                'subject_id': obj.subject.id,
                'subject_num': obj.subject.subject_num,
                'subject_name': obj.subject.subject_name,
                'type': obj.subject.get_balance_type_display(),
                'initial_date': datetime.strftime(soa_obj.date, '%Y-%m-%d'),
                'initial_abstract': '年初余额',
                'initial_debtor_amount': 0,
                'initial_credit_amount': 0,
                'initial_balance': obj.num * obj.money,
                'now_date': datetime.strftime(start_date,'%Y-%m-%d'),
                'now_abstract': '本期合计',
                'now_debtor_amount': now_obj[0]['debtor_amount'] if now_obj else 0,
                'now_credit_amount': now_obj[0]['debtor_amount'] if now_obj else 0,
                'now_balance': new_voucher_child_obj.balance if new_voucher_child_obj else obj.num * obj.money,
                'final_date': datetime.strftime(soa_obj.date, '%Y-%m-%d'),
                'final_abstract': '本年累计',
                'final_debtor_amount': year_obj[0]['debtor_amount'] if year_obj else 0,
                'final_credit_amount': year_obj[0]['credit_amount'] if year_obj else 0,
                'final_balance': obj.balance,
            }
            result.append(info)

        return common_response(data=result)

class SubjectAccountView(APIView):
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

        # 获取本期日期
        start_date = request.GET.get('date', date(date.today().year, date.today().month, 1))
        if isinstance(start_date, str) and start_date != '':
            date_list = start_date.split('-')
            start_date = date(int(date_list[0]), int(date_list[1]), 1)
        if start_date.month < 12:
            end_date = date(start_date.year, start_date.month+1, 1)
        else:
            end_date = date(start_date.year+1, 1, 1)

        # 本年日期
        year_start_date = date(soa_obj.date.year, 1, 1)
        year_end_date = date(soa_obj.date.year+1, 1, 1)

        # 期末日期
        final_start_date = date(soa_obj.date.year, 12, 1)
        final_end_date = date(soa_obj.date.year+1, 1, 1)

        result = []
        for sub_obj in Subject.objects.filter(subjectofaccounts__account=soa_obj, created_at__gte=year_start_date, created_at__lt=year_end_date):
            voucher_child_obj = VoucherChild.objects.filter(voucher__is_pal=False, subject=sub_obj)
            now_voucher_child_obj = voucher_child_obj.filter(add_date__gte=start_date, add_date__lt=end_date).values('subject__id').annotate(debtor_amount=Sum('debtor_money'), credit_amount=Sum('credit_money')).values('debtor_amount', 'credit_amount')
            year_voucher_child_obj = voucher_child_obj.filter(add_date__gte=year_start_date, add_date__lt=year_end_date).values('subject__id').annotate(debtor_amount=Sum('debtor_money'), credit_amount=Sum('credit_money')).values('debtor_amount', 'credit_amount')
            final_voucher_child_obj = voucher_child_obj.filter(add_date__gte=final_start_date, add_date__lt=final_end_date).values('subject__id').annotate(debtor_amount=Sum('debtor_money'), credit_amount=Sum('credit_money')).values('debtor_amount', 'credit_amount')
            info = {
                'number': sub_obj.subject_num,
                'subject_name': sub_obj.subject_name,
                'initial_debtor_money': 0,
                'initial_credit_money': 0,
                'now_debtor_money': now_voucher_child_obj[0]['debtor_amount'] if now_voucher_child_obj else 0,
                'now_credit_money': now_voucher_child_obj[0]['credit_amount'] if now_voucher_child_obj else 0,
                'year_debtor_money': year_voucher_child_obj[0]['debtor_amount'] if year_voucher_child_obj else 0,
                'year_credit_money': year_voucher_child_obj[0]['credit_amount'] if year_voucher_child_obj else 0,
                'final_debtor_money': final_voucher_child_obj[0]['debtor_amount'] if final_voucher_child_obj else 0,
                'final_credit_money': final_voucher_child_obj[0]['credit_amount'] if final_voucher_child_obj else 0,
            }
            result.append(info)

        return common_response(data=result)


class BusinessAccountView(APIView):
    def get(self, request):
        # 验证用户信息
        is_log, user_id = is_logined(request)
        try:
            obj = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return common_response(code=500, msg='用户不存在!')

        soa_id = request.GET.get('soa_id', '') # 帐套id
        business_id = request.GET.get('business_id', 1) # 帐套id
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
        start_date = request.GET.get('date', date(date.today().year, date.today().month, 1))
        if isinstance(start_date, str) and start_date != '':
            date_list = start_date.split('-')
            start_date = date(int(date_list[0]), int(date_list[1]), 1)
        if start_date.month < 12:
            end_date = date(start_date.year, start_date.month+1, 1)
        else:
            end_date = date(start_date.year+1, 1, 1)

        # 本年日期
        final_start_date = date(soa_obj.date.year, 1, 1)
        final_end_date = date(soa_obj.date.year+1, 1, 1)

        result = {}
        for sub_obj in business_obj.assists.all():
            voucher_child_obj = VoucherChild.objects.filter(voucher__is_pal=False, add_date__gte=start_date, add_date__lt=end_date, subject=sub_obj) 
            if not voucher_child_obj:
                continue

            if sub_obj.subject_name not in result:
                # 设置初期余额
                result[sub_obj.subject_name] = []
                subjectofaccount_obj = sub_obj.subjectofaccounts.filter(account=soa_id).first()
                info = {
                    'date': datetime.strftime(initial_start_date, '%Y-%m-%d'),
                    'voucher_word': '',
                    'abstract': '期初余额',
                    'debtor_money': 0,
                    'credit_money': 0,
                    'type': '平',
                    'balance': subjectofaccount_obj.num * subjectofaccount_obj.money,
                }
                result[sub_obj.subject_name].append(info)

            for obj in voucher_child_obj:
                vou_info = {
                    'date': datetime.strftime(obj.add_date, '%Y-%m-%d'),
                    'voucher_word': f'{obj.voucher.get_voucher_type_display()}-{obj.voucher.voucher_word}',
                    'abstract': obj.abstract,
                    'debtor_money': obj.debtor_money,
                    'credit_money': obj.credit_money,
                    'type': obj.subject.get_balance_type_display(),
                    'balance': obj.balance,
                }
                result[sub_obj.subject_name].append(vou_info)

            # 本期合计
            now_amount = voucher_child_obj.values('subject__id').annotate(debtor_amount=Sum('debtor_money'), credit_amount=Sum('credit_money')).values('subject', 'subject__subject_name', 'debtor_amount', 'credit_amount')
            new_voucher_child_obj = VoucherChild.objects.filter(voucher__is_pal=False, add_date__gte=start_date, add_date__lt=end_date).order_by('-created_at').first()
            now_info = {
                'date': datetime.strftime(start_date, '%Y-%m-%d'),
                'voucher_word': '',
                'abstract': '本期合计',
                'debtor_money': now_amount[0]['debtor_amount'],
                'credit_money': now_amount[0]['credit_amount'],
                'type': new_voucher_child_obj.subject.get_balance_type_display(),
                'balance': new_voucher_child_obj.balance,
            }
            result[sub_obj.subject_name].append(now_info)
            # 本年累计
            year_obj = VoucherChild.objects.filter(voucher__is_pal=False, add_date__gte=final_start_date, add_date__lt=final_end_date, subject=sub_obj).values('subject__id').annotate(debtor_amount=Sum('debtor_money'), credit_amount=Sum('credit_money')).values('subject', 'subject__subject_name', 'debtor_amount', 'credit_amount')
            year_voucher_child_obj = VoucherChild.objects.filter(voucher__is_pal=False, subject=sub_obj, add_date__gte=final_start_date, add_date__lt=final_end_date).order_by('-created_at').first()
            year_info = {
                'date': datetime.strftime(start_date, '%Y-%m-%d'),
                'voucher_word': '',
                'abstract': '本年累计',
                'debtor_money': year_obj[0]['debtor_amount'],
                'credit_money': year_obj[0]['credit_amount'],
                'type': year_voucher_child_obj.subject.get_balance_type_display(),
                'balance': year_voucher_child_obj.balance,
            }
            result[sub_obj.subject_name].append(year_info)

        return common_response(data=result)


class BusinessBalanceView(APIView):
    def get(self, request):
        # 验证用户信息
        is_log, user_id = is_logined(request)
        try:
            obj = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return common_response(code=500, msg='用户不存在!')

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
        start_date = request.GET.get('date', date(date.today().year, date.today().month, 1))
        if isinstance(start_date, str) and start_date != '':
            date_list = start_date.split('-')
            start_date = date(int(date_list[0]), int(date_list[1]), 1)
        if start_date.month < 12:
            end_date = date(start_date.year, start_date.month+1, 1)
        else:
            end_date = date(start_date.year+1, 1, 1)

        # 本年日期
        year_start_date = date(soa_obj.date.year, 1, 1)
        year_end_date = date(soa_obj.date.year+1, 1, 1)

        # 期末日期
        final_start_date = date(soa_obj.date.year, 12, 1)
        final_end_date = date(soa_obj.date.year+1, 1, 1)

        result = []
        amount_info = {
            'number': '',
            'subject_name': '合计',
            'initial_debtor_money': 0,
            'initial_credit_money': 0,
            'now_debtor_money': 0,
            'now_credit_money': 0,
            'year_debtor_money': 0,
            'year_credit_money': 0,
            'final_debtor_money': 0,
            'final_credit_money': 0
        }
        for sub_obj in business_obj.assists.all():
            voucher_child_obj = VoucherChild.objects.filter(voucher__is_pal=False, subject=sub_obj)
            now_voucher_child_obj = voucher_child_obj.filter(add_date__gte=start_date, add_date__lt=end_date).values('subject__id').annotate(debtor_amount=Sum('debtor_money'), credit_amount=Sum('credit_money')).values('debtor_amount', 'credit_amount')
            year_voucher_child_obj = voucher_child_obj.filter(add_date__gte=year_start_date, add_date__lt=year_end_date).values('subject__id').annotate(debtor_amount=Sum('debtor_money'), credit_amount=Sum('credit_money')).values('debtor_amount', 'credit_amount')
            final_voucher_child_obj = voucher_child_obj.filter(add_date__gte=final_start_date, add_date__lt=final_end_date).values('subject__id').annotate(debtor_amount=Sum('debtor_money'), credit_amount=Sum('credit_money')).values('debtor_amount', 'credit_amount')
            info = {
                'number': sub_obj.subject_num,
                'subject_name': sub_obj.subject_name,
                'initial_debtor_money': 0,
                'initial_credit_money': 0,
                'now_debtor_money': now_voucher_child_obj[0]['debtor_amount'] if now_voucher_child_obj else 0,
                'now_credit_money': now_voucher_child_obj[0]['credit_amount'] if now_voucher_child_obj else 0,
                'year_debtor_money': year_voucher_child_obj[0]['debtor_amount'] if year_voucher_child_obj else 0,
                'year_credit_money': year_voucher_child_obj[0]['credit_amount'] if year_voucher_child_obj else 0,
                'final_debtor_money': final_voucher_child_obj[0]['debtor_amount'] if final_voucher_child_obj else 0,
                'final_credit_money': final_voucher_child_obj[0]['credit_amount'] if final_voucher_child_obj else 0,
            }
            amount_info['now_debtor_money'] += info['now_debtor_money']
            amount_info['now_credit_money'] += info['now_credit_money']
            amount_info['year_debtor_money'] += info['year_debtor_money']
            amount_info['year_credit_money'] += info['year_credit_money']
            amount_info['final_debtor_money'] += info['final_debtor_money']
            amount_info['final_credit_money'] += info['final_credit_money']
            result.append(info)
        result.append(amount_info)
        return common_response(data=result)


class ReportView(APIView):
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

        # 获取本期日期
        start_date = request.GET.get('date', date(date.today().year, date.today().month, 1))
        if isinstance(start_date, str):
            date_list = start_date.split('-')
            start_date = date(int(date_list[0]), int(date_list[1]), 1)
        if start_date.month < 12:
            end_date = date(start_date.year, start_date.month+1, 1)
        else:
            end_date = date(start_date.year+1, 1, 1)

        # 获取资产分类下所有的科目
        row = 1
        assets_list = []
        for sub_obj in SubjectOfAccounts.objects.filter(account=soa_obj, subject__subject_type=0):
            info = {
                'subject_name': sub_obj.subject.subject_name,
                'row': row,
                'start_money': sub_obj.num * sub_obj.money,
                'end_money': sub_obj.balance
            }
            row += 1
            assets_list.append(info)

        # 负债
        liabilities_list = []
        for sub_obj in SubjectOfAccounts.objects.filter(account=soa_obj, subject__subject_type=2):
            info = {
                'subject_name': sub_obj.subject.subject_name,
                'row': row,
                'start_money': sub_obj.num * sub_obj.money,
                'end_money': sub_obj.balance
            }
            row += 1
            liabilities_list.append(info)

        result = {'assets_list': assets_list, 'liabilities_list': liabilities_list}
        return common_response(data=result)


class ProfitView(APIView):
    def get(self, request):
        ''' 利润表 '''
        soa_id = request.GET.get('soa_id', '') # 帐套id
        if not soa_id:
            return common_response(code=500, msg='缺少帐套id')

        try:
            soa_obj = SetOfAccounts.objects.get(id=soa_id)
        except SetOfAccounts.DoesNotExist:
            return common_response(code=500, msg='帐套id不存在')

        start_date = request.GET.get('date', date(date.today().year, date.today().month, 1))
        if isinstance(start_date, str):
            date_list = start_date.split('-')
            start_date = date(int(date_list[0]), int(date_list[1]), 1)
        end_date = date(start_date.year, start_date.month+1, 1)

        row = 1
        profit_list = []
        for sub_obj in SubjectOfAccounts.objects.filter(account=soa_obj, subject__subject_type=4):
            # 计算本月金额
            voucher_child = VoucherChild.objects.filter(voucher__is_pal=False, subject=sub_obj.subject, created_at__gte=start_date, created_at__lt=end_date).values('subject__id').annotate(debtor_amount=Sum('debtor_money'), credit_amount=Sum('credit_money')).values('debtor_amount', 'credit_amount')
            end_money = 0
            if sub_obj.subject.balance_type == 0:
                # 借 贷=减 借=加
                end_money += voucher_child.debtor_money if hasattr(voucher_child, 'debtor_money') else 0
                end_money -= voucher_child.credit_money if hasattr(voucher_child, 'credit_money') else 0
            else:
                # 贷
                end_money -= voucher_child.debtor_money if hasattr(voucher_child, 'debtor_money') else 0
                end_money += voucher_child.credit_money if hasattr(voucher_child, 'credit_money') else 0              

            info = {
                'subject_name': sub_obj.subject.subject_name,
                'row': row,
                'year_money': sub_obj.balance,
                'end_money': end_money
            }
            row += 1
            profit_list.append(info)
        return common_response(data=profit_list)
