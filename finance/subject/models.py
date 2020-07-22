from django.db import models
from django.utils import timezone
from user.models import Village


SUBJECT_TYPE = (
    (0, '资产'),
    (1, '负债'),
    (2, '权益'),
    (3, '成本'),
    (4, '损益')
)

BALANCE_TYPE = (
    (0, '借'),
    (1, '贷')
)


class Assist(models.Model):
    assist_name = models.CharField("辅助核算名称", max_length=128)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class SetOfAccounts(models.Model):
    name = models.CharField("帐期名称", max_length=128)
    date = models.DateField('帐期')
    village = models.ForeignKey(Village, related_name='soa', on_delete=models.CASCADE)
    is_shield = models.BooleanField("是否屏蔽", default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class Subject(models.Model):
    subject_num = models.CharField("科目编码", max_length=128)
    subject_name = models.CharField("科目名称", max_length=128)
    parent = models.ForeignKey("self", related_name='child_categories', null=True, blank=True, on_delete=models.CASCADE)
    subject_type = models.SmallIntegerField("科目类别", choices=SUBJECT_TYPE, default=0)
    balance_type = models.SmallIntegerField("余额方向", choices=BALANCE_TYPE, default=0)
    assist_business = models.ManyToManyField(Assist, related_name="assists", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def assist_list(self):
        ass_list = [ass.id for ass in self.assist_business.all()]
        return ass_list


class SubjectOfAccounts(models.Model):
    account = models.ForeignKey(SetOfAccounts, related_name='accountofsubjects', on_delete=models.CASCADE)
    subject = models.OneToOneField(Subject, related_name='subjectofaccounts', on_delete=models.CASCADE)
    num = models.IntegerField('科目数量', default=0)
    money = models.DecimalField("科目金额", max_digits=7, decimal_places=2)


class SubjectLog(models.Model):
    money = models.DecimalField("增减金额", max_digits=7, decimal_places=2)
    balance = models.DecimalField("当前科目剩余金额", max_digits=7, decimal_places=2)
    subject = models.ForeignKey(SubjectOfAccounts, related_name='balancelog', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

