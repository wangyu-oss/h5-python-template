import secrets

from django.db import models
from django.utils import timezone

from common.models import SoftDeleteModel, TimeStampedModel
from common.security import mask_id_card, mask_phone


def new_token():
    return secrets.token_hex(32)


class Tenant(SoftDeleteModel):
    name = models.CharField(max_length=64)
    code = models.CharField(max_length=64, unique=True)
    status = models.CharField(max_length=16, default='active')
    expire_at = models.DateField(null=True, blank=True)

    def public(self):
        return {
            'id': self.id,
            'name': self.name,
            'code': self.code,
            'status': self.status,
            'expire_at': self.expire_at.isoformat() if self.expire_at else '',
        }


class Department(SoftDeleteModel):
    tenant = models.ForeignKey('Tenant', null=True, blank=True, on_delete=models.CASCADE, related_name='departments')
    name = models.CharField(max_length=64)
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='children')
    sort = models.IntegerField(default=0)

    class Meta:
        ordering = ['sort', 'id']

    def public(self):
        return {'id': self.id, 'name': self.name, 'parent_id': self.parent_id, 'sort': self.sort}


class UserGroup(SoftDeleteModel):
    tenant = models.ForeignKey(Tenant, null=True, blank=True, on_delete=models.CASCADE, related_name='groups')
    name = models.CharField(max_length=64)
    code = models.CharField(max_length=64, unique=True)

    def public(self):
        return {'id': self.id, 'name': self.name, 'code': self.code}


class Account(SoftDeleteModel):
    username = models.CharField(max_length=64, unique=True)
    password = models.CharField(max_length=255, blank=True, default='')
    display_name = models.CharField(max_length=64, blank=True, default='')
    phone = models.CharField(max_length=32, blank=True, default='', db_index=True)
    email = models.CharField(max_length=128, blank=True, default='')
    avatar = models.CharField(max_length=255, blank=True, default='')
    gender = models.CharField(max_length=16, blank=True, default='')
    birthday = models.DateField(null=True, blank=True)
    tenant = models.ForeignKey(Tenant, null=True, blank=True, on_delete=models.CASCADE, related_name='accounts')
    dept = models.ForeignKey(Department, null=True, blank=True, on_delete=models.SET_NULL)
    last_login_ip = models.CharField(max_length=64, blank=True, default='')
    groups = models.ManyToManyField(UserGroup, blank=True, related_name='accounts')
    roles = models.ManyToManyField('rbac.Role', blank=True, related_name='accounts')
    tags = models.JSONField(default=list, blank=True)
    status = models.CharField(max_length=16, default='active')
    is_super = models.BooleanField(default=False)
    is_guest = models.BooleanField(default=False)
    failed_logins = models.IntegerField(default=0)
    locked_until = models.DateTimeField(null=True, blank=True)
    real_name = models.CharField(max_length=64, blank=True, default='')
    id_card = models.CharField(max_length=32, blank=True, default='')
    realname_status = models.CharField(max_length=16, blank=True, default='')

    class Meta:
        ordering = ['id']

    def public(self, mask=True):
        phone = mask_phone(self.phone) if mask else self.phone
        return {
            'id': self.id,
            'username': self.username,
            'display_name': self.display_name or self.username,
            'phone': phone,
            'email': self.email,
            'avatar': self.avatar,
            'gender': self.gender,
            'birthday': self.birthday.isoformat() if self.birthday else '',
            'dept_id': self.dept_id,
            'dept_name': self.dept.name if self.dept_id else '',
            'group_ids': list(self.groups.values_list('id', flat=True)),
            'role_ids': list(self.roles.values_list('id', flat=True)),
            'tags': self.tags or [],
            'status': self.status,
            'is_super': self.is_super,
            'is_guest': self.is_guest,
            'tenant_id': self.tenant_id,
            'tenant_name': self.tenant.name if self.tenant_id else '',
            'real_name': self.real_name,
            'id_card': mask_id_card(self.id_card) if mask else self.id_card,
            'realname_status': self.realname_status,
            'created_at': timezone.localtime(self.created_at).strftime('%Y-%m-%d %H:%M:%S') if self.created_at else '',
        }


class Session(models.Model):
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='sessions')
    access_token = models.CharField(max_length=64, unique=True, default=new_token)
    refresh_token = models.CharField(max_length=64, unique=True, default=new_token)
    ip = models.CharField(max_length=64, blank=True, default='')
    user_agent = models.CharField(max_length=255, blank=True, default='')
    revoked = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    access_expires = models.DateTimeField()
    refresh_expires = models.DateTimeField()


class SmsCode(models.Model):
    phone = models.CharField(max_length=32, db_index=True)
    code_hash = models.CharField(max_length=64)
    purpose = models.CharField(max_length=32, default='login')
    used = models.BooleanField(default=False)
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)


class WechatBind(TimeStampedModel):
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='wechat_binds')
    platform = models.CharField(max_length=16)
    openid = models.CharField(max_length=64)
    unionid = models.CharField(max_length=64, blank=True, default='')

    class Meta:
        unique_together = [('platform', 'openid')]


class Draft(TimeStampedModel):
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='drafts')
    key = models.CharField(max_length=64)
    content = models.TextField(blank=True, default='')

    class Meta:
        unique_together = [('account', 'key')]
