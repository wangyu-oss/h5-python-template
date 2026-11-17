from django.db import models

from common.models import TimeStampedModel
from system.models import fmt


class MessageTemplate(TimeStampedModel):
    tenant = models.ForeignKey('accounts.Tenant', null=True, blank=True, on_delete=models.CASCADE, related_name='templates')
    code = models.CharField(max_length=64)
    channel = models.CharField(max_length=16, default='inbox')
    title = models.CharField(max_length=120, blank=True, default='')
    content = models.TextField(blank=True, default='')
    enabled = models.BooleanField(default=True)

    def public(self):
        return {
            'id': self.id,
            'code': self.code,
            'channel': self.channel,
            'title': self.title,
            'content': self.content,
            'enabled': self.enabled,
        }


class InboxMessage(TimeStampedModel):
    tenant = models.ForeignKey('accounts.Tenant', null=True, blank=True, on_delete=models.CASCADE, related_name='messages')
    account = models.ForeignKey('accounts.Account', on_delete=models.CASCADE, related_name='messages')
    title = models.CharField(max_length=120)
    content = models.TextField(blank=True, default='')
    category = models.CharField(max_length=16, default='system')
    is_read = models.BooleanField(default=False)
    expire_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-id']

    def public(self):
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'category': self.category,
            'is_read': self.is_read,
            'created_at': fmt(self.created_at),
        }


class MessageSendLog(models.Model):
    tenant = models.ForeignKey('accounts.Tenant', null=True, blank=True, on_delete=models.CASCADE)
    channel = models.CharField(max_length=16, default='sms')
    target = models.CharField(max_length=128, blank=True, default='')
    content = models.TextField(blank=True, default='')
    success = models.BooleanField(default=False)
    retries = models.IntegerField(default=0)
    error = models.CharField(max_length=200, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-id']

    def public(self):
        return {
            'id': self.id,
            'channel': self.channel,
            'target': self.target,
            'content': self.content,
            'success': self.success,
            'retries': self.retries,
            'error': self.error,
            'created_at': fmt(self.created_at),
        }
