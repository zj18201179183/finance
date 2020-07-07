from django.db import models
from django.utils import timezone


USER_SEX_CHOICES = (
    (0, '未知'),
    (1, '男性'),
    (2, '女性')
)

IDENTITY_CHOICES = (
    (0, '管理员'),
    (1, '财务管理人员'),
    (2, '财务主管')
)

class User(models.Model):
    username = models.CharField("username", max_length=32)
    password = models.CharField("password", max_length=128)
    identity = models.SmallIntegerField("identity", choices=IDENTITY_CHOICES, default=0)
    photo = models.ImageField(upload_to='./static/image/user', null=True, blank=True)
    phone_number = models.CharField("phone number", max_length=15, unique=True)
    sex = models.SmallIntegerField("sex", choices=USER_SEX_CHOICES, default=0)
    last_login = models.DateTimeField("last login")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.username

    class Meta:
        verbose_name = '用户'
        verbose_name_plural = '用户'

    def image_url(self):
        # if self.photo:
        #     return self.photo
        return '#'