from user.models import *
from subject.models import *

def create_user():
    # 创建超级用户
    user_obj = User.objects.create(
        username = 'admin',
        password = '1234qwer',
        is_admin = True,
        phone_number = 13333333333
    )
    user_obj.save()

def create_permission():
    permission_data = [
        {
            'group_name': '辅助核算增加',
            'api_name': 'Assis',
            'method': 'POST'
        },
        {
            'group_name': '辅助核算删除',
            'api_name': 'Assis',
            'method': 'DELETE'
        },
        {
            'group_name': '辅助核算修改',
            'api_name': 'Assis',
            'method': 'PUT'
        },
        {
            'group_name': '辅助核算查找',
            'api_name': 'Assis',
            'method': 'GET'
        },
        {
            'group_name': '帐套增加',
            'api_name': 'SetOfAccounts',
            'method': 'POST'
        },
        {
            'group_name': '帐套删除',
            'api_name': 'SetOfAccounts',
            'method': 'DELETE'
        },
        {
            'group_name': '帐套修改',
            'api_name': 'SetOfAccounts',
            'method': 'PUT'
        },
        {
            'group_name': '帐套查找',
            'api_name': 'SetOfAccounts',
            'method': 'GET'
        },
        {
            'group_name': '凭证增加',
            'api_name': 'Voucher',
            'method': 'POST'
        },
        {
            'group_name': '凭证删除',
            'api_name': 'Voucher',
            'method': 'DELETE'
        },
        {
            'group_name': '凭证修改',
            'api_name': 'Voucher',
            'method': 'PUT'
        },
        {
            'group_name': '凭证查找',
            'api_name': 'Voucher',
            'method': 'GET'
        },
        {
            'group_name': '科目删除',
            'api_name': 'Subject',
            'method': 'POST'
        },
        {
            'group_name': '科目修改',
            'api_name': 'Subject',
            'method': 'PUT'
        },
        {
            'group_name': '科目查找',
            'api_name': 'Subject',
            'method': 'GET'
        },
        {
            'group_name': '凭证审核',
            'api_name': 'VoucherCheck',
            'method': 'GET'
        },
        {
            'group_name': '结转损益',
            'api_name': 'Transfer',
            'method': 'GET'
        },
        {
            'group_name': '查看初始金额',
            'api_name': 'SetSubjectMoney',
            'method': 'GET'
        },
        {
            'group_name': '设置初始金额',
            'api_name': 'SetSubjectMoney',
            'method': 'PUT'
        },
        {
            'group_name': '用户屏蔽',
            'api_name': 'UserShield',
            'method': 'PUT'
        }
    ]

    # 创建权限
    for obj in permission_data: 
        per_obj = Permission.objects.create( 
            permission_name=obj['group_name'], 
            api_name=obj['api_name'], 
            method=obj['method'] 
        ) 
        per_obj.save() 


def create_subject():
    # 创建科目
    subject_data = [
        {
            'subject_num' : '101',
            'subject_name' : '现金',
            'balance_type' : 0,
            'subject_type' : 0
        },
        {
            'subject_num' : '102',
            'subject_name' : '银行存款',
            'balance_type' : 0,
            'subject_type' : 0
        },
        {
            'subject_num' : '111',
            'subject_name' : '短期投资',
            'balance_type' : 0,
            'subject_type' : 0
        },
        {
            'subject_num' : '112',
            'subject_name' : '应收款',
            'balance_type' : 0,
            'subject_type' : 0
        },
        {
            'subject_num' : '113',
            'subject_name' : '内部往来',
            'balance_type' : 0,
            'subject_type' : 0
        },
        {
            'subject_num' : '121',
            'subject_name' : '库存物质',
            'balance_type' : 0,
            'subject_type' : 0
        },
        {
            'subject_num' : '131',
            'subject_name' : '牧畜(禽)资产',
            'balance_type' : 0,
            'subject_type' : 0
        },
        {
            'subject_num' : '132',
            'subject_name' : '林木资产',
            'balance_type' : 0,
            'subject_type' : 0
        },
        {
            'subject_num' : '141',
            'subject_name' : '长期投资',
            'balance_type' : 0,
            'subject_type' : 0
        },
        {
            'subject_num' : '151',
            'subject_name' : '固定资产',
            'balance_type' : 0,
            'subject_type' : 0
        },
        {
            'subject_num' : '152',
            'subject_name' : '累计折扣',
            'balance_type' : 0,
            'subject_type' : 0
        },
        {
            'subject_num' : '153',
            'subject_name' : '固定资产清理',
            'balance_type' : 0,
            'subject_type' : 0
        },
        {
            'subject_num' : '154',
            'subject_name' : '在建工程',
            'balance_type' : 0,
            'subject_type' : 0
        },
        {
            'subject_num' : '201',
            'subject_name' : '短期借款',
            'balance_type' : 1,
            'subject_type' : 1
        },
        {
            'subject_num' : '202',
            'subject_name' : '应付款',
            'balance_type' : 1,
            'subject_type' : 1
        },
        {
            'subject_num' : '211',
            'subject_name' : '应付工资',
            'balance_type' : 1,
            'subject_type' : 1
        },
        {
            'subject_num' : '212',
            'subject_name' : '应付福利费',
            'balance_type' : 1,
            'subject_type' : 1
        },
        {
            'subject_num' : '221',
            'subject_name' : '长期借款及应付款',
            'balance_type' : 1,
            'subject_type' : 1
        },
        {
            'subject_num' : '231',
            'subject_name' : '一事一议资金',
            'balance_type' : 1,
            'subject_type' : 1
        },
        {
            'subject_num' : '301',
            'subject_name' : '资本',
            'balance_type' : 1,
            'subject_type' : 2
        },
        {
            'subject_num' : '311',
            'subject_name' : '公积金益金',
            'balance_type' : 1,
            'subject_type' : 2
        },
        {
            'subject_num' : '321',
            'subject_name' : '本年收益',
            'balance_type' : 1,
            'subject_type' : 2
        },
        {
            'subject_num' : '322',
            'subject_name' : '收益分配',
            'balance_type' : 1,
            'subject_type' : 2
        },
        {
            'subject_num' : '401',
            'subject_name' : '生产(劳务)成本',
            'balance_type' : 0,
            'subject_type' : 3
        },
        {
            'subject_num' : '501',
            'subject_name' : '经营收入',
            'balance_type' : 1,
            'subject_type' : 4
        },
        {
            'subject_num' : '502',
            'subject_name' : '经营支出',
            'balance_type' : 0,
            'subject_type' : 4
        },
        {
            'subject_num' : '511',
            'subject_name' : '发包及上交收入',
            'balance_type' : 1,
            'subject_type' : 4
        },
        {
            'subject_num' : '521',
            'subject_name' : '农业税附加返还收入',
            'balance_type' : 1,
            'subject_type' : 4
        },
        {
            'subject_num' : '522',
            'subject_name' : '补助收入',
            'balance_type' : 1,
            'subject_type' : 4
        },
        {
            'subject_num' : '531',
            'subject_name' : '其他收入',
            'balance_type' : 1,
            'subject_type' : 4
        },
        {
            'subject_num' : '541',
            'subject_name' : '管理费用',
            'balance_type' : 1,
            'subject_type' : 4
        },
        {
            'subject_num' : '551',
            'subject_name' : '其他支出',
            'balance_type' : 0,
            'subject_type' : 4
        },
        {
            'subject_num' : '561',
            'subject_name' : '投资收益',
            'balance_type' : 1,
            'subject_type' : 4
        }
    ]

    for obj in subject_data: 
        subject_obj = Subject.objects.create( 
            subject_num=obj['subject_num'], 
            subject_name=obj['subject_name'], 
            subject_type=obj['subject_type'], 
            balance_type=obj['balance_type'] 
        ) 
        subject_obj.save() 