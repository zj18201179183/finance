from django.db import models
from django.utils import timezone
from .func import ImageStorage


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


class Village(models.Model):
    number = models.CharField("number", max_length=128)
    name = models.CharField("username", max_length=128)
    parent = models.ForeignKey("self", related_name='child_villages', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class User(models.Model):
    username = models.CharField("username", max_length=32)
    password = models.CharField("password", max_length=128)
    identity = models.SmallIntegerField("identity", choices=IDENTITY_CHOICES, default=0)
    photo = models.ImageField(upload_to='./static/image/user', storage=ImageStorage(), null=True, blank=True)
    phone_number = models.CharField("phone number", max_length=15, unique=True)
    is_shield = models.BooleanField("是否屏蔽", default=False)
    sex = models.SmallIntegerField("sex", choices=USER_SEX_CHOICES, default=0)
    village = models.ForeignKey(Village, related_name='users')
    last_login = models.DateTimeField("last login")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.username

    class Meta:
        verbose_name = '用户'
        verbose_name_plural = '用户'

    def image_url(self):
        return self.photo.url if self.photo else ''
