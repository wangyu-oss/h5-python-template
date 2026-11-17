from django.db import models
from django.utils import timezone

from common.models import SoftDeleteModel, TimeStampedModel


def plain_text(value):
    text = value or ''
    while '<' in text and '>' in text:
        start = text.find('<')
        end = text.find('>', start)
        if end < 0:
            break
        text = text[:start] + text[end + 1:]
    return ' '.join(text.split())


def fmt(value):
    if not value:
        return ''
    if getattr(value, 'tzinfo', None) is not None:
        value = timezone.localtime(value)
    if hasattr(value, 'hour'):
        return value.strftime('%Y-%m-%d %H:%M:%S')
    return value.strftime('%Y-%m-%d')


class Setting(models.Model):
    tenant = models.ForeignKey('accounts.Tenant', null=True, blank=True, on_delete=models.CASCADE, related_name='settings')
    key = models.CharField(max_length=64)
    value = models.TextField(blank=True, default='')
    remark = models.CharField(max_length=200, blank=True, default='')
    category = models.CharField(max_length=16, blank=True, default='basic')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['key'], condition=models.Q(tenant__isnull=True), name='setting_platform_key'),
            models.UniqueConstraint(fields=['tenant', 'key'], name='setting_tenant_key'),
        ]

    def public(self):
        return {'key': self.key, 'value': self.value, 'remark': self.remark, 'category': self.category, 'tenant_id': self.tenant_id}


class SettingChange(models.Model):
    tenant = models.ForeignKey('accounts.Tenant', null=True, blank=True, on_delete=models.CASCADE)
    account = models.ForeignKey('accounts.Account', null=True, blank=True, on_delete=models.SET_NULL)
    key = models.CharField(max_length=64)
    old_value = models.TextField(blank=True, default='')
    new_value = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-id']

    def public(self):
        return {
            'id': self.id,
            'key': self.key,
            'old_value': self.old_value,
            'new_value': self.new_value,
            'username': self.account.username if self.account_id else '',
            'created_at': fmt(self.created_at),
        }


class Banner(SoftDeleteModel):
    tenant = models.ForeignKey('accounts.Tenant', null=True, blank=True, on_delete=models.CASCADE, related_name='banners')
    title = models.CharField(max_length=80)
    image = models.CharField(max_length=255, blank=True, default='')
    link = models.CharField(max_length=255, blank=True, default='')
    color = models.CharField(max_length=16, default='#1989fa')
    sort = models.IntegerField(default=0)
    enabled = models.BooleanField(default=True)
    jump_type = models.CharField(max_length=16, default='page')
    start_at = models.DateTimeField(null=True, blank=True)
    end_at = models.DateTimeField(null=True, blank=True)
    pinned = models.BooleanField(default=False)

    class Meta:
        ordering = ['sort', 'id']

    def public(self):
        return {
            'id': self.id,
            'title': self.title,
            'image': self.image,
            'link': self.link,
            'color': self.color,
            'sort': self.sort,
            'enabled': self.enabled,
            'jump_type': self.jump_type,
            'start_at': fmt(self.start_at),
            'end_at': fmt(self.end_at),
            'pinned': self.pinned,
            'is_deleted': self.is_deleted,
        }


class Announcement(SoftDeleteModel):
    tenant = models.ForeignKey('accounts.Tenant', null=True, blank=True, on_delete=models.CASCADE, related_name='announcements')
    title = models.CharField(max_length=120)
    content = models.TextField(blank=True, default='')
    enabled = models.BooleanField(default=True)
    jump_type = models.CharField(max_length=16, default='none')
    start_at = models.DateTimeField(null=True, blank=True)
    end_at = models.DateTimeField(null=True, blank=True)
    pinned = models.BooleanField(default=False)

    class Meta:
        ordering = ['-id']

    def public(self, detail=False):
        data = {
            'id': self.id,
            'title': self.title,
            'enabled': self.enabled,
            'jump_type': self.jump_type,
            'pinned': self.pinned,
            'is_deleted': self.is_deleted,
            'created_at': fmt(self.created_at),
        }
        if detail:
            data['content'] = self.content
        else:
            data['summary'] = plain_text(self.content)[:80]
        return data


class DictType(SoftDeleteModel):
    tenant = models.ForeignKey('accounts.Tenant', null=True, blank=True, on_delete=models.CASCADE, related_name='dict_types')
    name = models.CharField(max_length=64)
    code = models.CharField(max_length=64, unique=True)

    def public(self):
        return {'id': self.id, 'name': self.name, 'code': self.code}


class DictItem(SoftDeleteModel):
    dict_type = models.ForeignKey(DictType, on_delete=models.CASCADE, related_name='items')
    label = models.CharField(max_length=64)
    value = models.CharField(max_length=64)
    sort = models.IntegerField(default=0)
    enabled = models.BooleanField(default=True)

    class Meta:
        ordering = ['sort', 'id']

    def public(self):
        return {
            'id': self.id,
            'dict_type_id': self.dict_type_id,
            'code': self.dict_type.code,
            'label': self.label,
            'value': self.value,
            'sort': self.sort,
            'enabled': self.enabled,
        }


class Region(models.Model):
    tenant = models.ForeignKey('accounts.Tenant', null=True, blank=True, on_delete=models.CASCADE, related_name='regions')
    code = models.CharField(max_length=12)
    name = models.CharField(max_length=64)
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='children')

    class Meta:
        ordering = ['code']

    def public(self):
        return {'id': self.id, 'code': self.code, 'name': self.name, 'parent_id': self.parent_id}


class LoginLog(models.Model):
    tenant = models.ForeignKey('accounts.Tenant', null=True, blank=True, on_delete=models.CASCADE, related_name='login_logs')
    username = models.CharField(max_length=64, blank=True, default='')
    success = models.BooleanField(default=False)
    message = models.CharField(max_length=200, blank=True, default='')
    ip = models.CharField(max_length=64, blank=True, default='')
    user_agent = models.CharField(max_length=255, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-id']

    def public(self):
        return {
            'id': self.id,
            'username': self.username,
            'success': self.success,
            'message': self.message,
            'ip': self.ip,
            'user_agent': self.user_agent,
            'created_at': fmt(self.created_at),
        }


class OperationLog(models.Model):
    tenant = models.ForeignKey('accounts.Tenant', null=True, blank=True, on_delete=models.CASCADE, related_name='operation_logs')
    account = models.ForeignKey('accounts.Account', null=True, blank=True, on_delete=models.SET_NULL)
    action = models.CharField(max_length=64)
    target = models.CharField(max_length=120, blank=True, default='')
    detail = models.TextField(blank=True, default='')
    ip = models.CharField(max_length=64, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-id']

    def public(self):
        return {
            'id': self.id,
            'username': self.account.username if self.account_id else '',
            'action': self.action,
            'target': self.target,
            'detail': self.detail,
            'ip': self.ip,
            'created_at': fmt(self.created_at),
        }


class ApiLog(models.Model):
    tenant = models.ForeignKey('accounts.Tenant', null=True, blank=True, on_delete=models.CASCADE, related_name='api_logs')
    trace_id = models.CharField(max_length=64, blank=True, default='')
    account = models.ForeignKey('accounts.Account', null=True, blank=True, on_delete=models.SET_NULL)
    method = models.CharField(max_length=8)
    path = models.CharField(max_length=255)
    status_code = models.IntegerField(default=0)
    duration_ms = models.IntegerField(default=0)
    ip = models.CharField(max_length=64, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-id']

    def public(self):
        return {
            'id': self.id,
            'trace_id': self.trace_id,
            'username': self.account.username if self.account_id else '',
            'method': self.method,
            'path': self.path,
            'status_code': self.status_code,
            'duration_ms': self.duration_ms,
            'ip': self.ip,
            'created_at': fmt(self.created_at),
        }
