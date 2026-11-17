from django.db import models

from common.models import TimeStampedModel
from system.models import fmt


class FileRecord(TimeStampedModel):
    tenant = models.ForeignKey('accounts.Tenant', null=True, blank=True, on_delete=models.CASCADE, related_name='files')
    owner = models.ForeignKey('accounts.Account', null=True, blank=True, on_delete=models.SET_NULL)
    name = models.CharField(max_length=255)
    path = models.CharField(max_length=255)
    size = models.IntegerField(default=0)
    content_type = models.CharField(max_length=128, blank=True, default='')
    storage = models.CharField(max_length=16, default='local')
    category = models.CharField(max_length=32, blank=True, default='default')
    is_private = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        ordering = ['-id']

    def public(self):
        return {
            'id': self.id,
            'name': self.name,
            'size': self.size,
            'content_type': self.content_type,
            'storage': self.storage,
            'category': self.category,
            'is_private': self.is_private,
            'url': f'/api/v1/files/{self.id}/raw',
            'created_at': fmt(self.created_at),
        }


class FileAccessLog(models.Model):
    file = models.ForeignKey(FileRecord, on_delete=models.CASCADE, related_name='access_logs')
    account = models.ForeignKey('accounts.Account', null=True, blank=True, on_delete=models.SET_NULL)
    ip = models.CharField(max_length=64, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
