from django.db import models
from django.utils import timezone
from user.models import User
from subject.models import Subject, SetOfAccounts


VOUCHER_TYPE = (
    (0, '记'),
    (1, '收'),
    (2, '付'),
    (3, '转')
)


class Voucher(models.Model):
    voucher_type = models.SmallIntegerField("凭证字", choices=VOUCHER_TYPE, default=0)
    voucher_word = models.CharField("凭证字号", null=True, max_length=128)
    soa = models.ForeignKey(SetOfAccounts, related_name='accountofvouchers', on_delete=models.CASCADE)
    created_user = models.ForeignKey(User, related_name='creators', on_delete=models.CASCADE)
    check_user = models.ForeignKey(User, related_name='checkers', null=True, blank=True, on_delete=models.CASCADE)
    voucher_date = models.DateField('凭证日期')
    is_audit = models.BooleanField("是否已审核", default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class VoucherChild(models.Model):
    abstract = models.CharField("摘要", null=True, max_length=128)
    voucher = models.ForeignKey(Voucher, related_name='vouchilds', on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, related_name='subjects', on_delete=models.CASCADE)
    debtor_money = models.DecimalField("借方金额", max_digits=7, decimal_places=2)
    credit_money =models.DecimalField("贷方金额", max_digits=7, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)



