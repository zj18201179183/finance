from django.db import models
from django.utils import timezone
from .func import ImageStorage


class Village(models.Model):
    number = models.CharField("number", max_length=128)
    name = models.CharField("username", max_length=128)
    parent = models.ForeignKey("self", related_name='child_villages', null=True, blank=True, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class Permission(models.Model):
    permission_name = models.CharField("权限名称", max_length=32)
    api_name = models.CharField("方法名", max_length=32)
    method = models.CharField("请求方法", max_length=32)


class Group(models.Model):
    group_name = models.CharField("身份名称", max_length=32)
    permission = models.ManyToManyField(Permission, related_name="groups")


class User(models.Model):
    username = models.CharField("username", max_length=32, unique=True)
    password = models.CharField("password", max_length=128)
    group = models.ForeignKey(Group, related_name='users', on_delete=models.CASCADE, null=True)
    photo = models.ImageField(upload_to='./static/image/user', storage=ImageStorage(), null=True, blank=True)
    phone_number = models.CharField("phone number", max_length=15, unique=True)
    is_shield = models.BooleanField("是否屏蔽", default=False)
    village = models.ForeignKey(Village, related_name='users', on_delete=models.CASCADE, null=True)
    is_admin = models.BooleanField("是否为超级管理员", default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.username

    class Meta:
        verbose_name = '用户'
        verbose_name_plural = '用户'

    def image_url(self):
        return self.photo.url if self.photo else ''
