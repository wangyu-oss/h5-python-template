from django.db import models

from system.models import fmt


class TrackCatalog(models.Model):
    tenant = models.ForeignKey('accounts.Tenant', null=True, blank=True, on_delete=models.CASCADE, related_name='track_catalogs')
    name = models.CharField(max_length=64)
    title = models.CharField(max_length=80, blank=True, default='')
    enabled = models.BooleanField(default=True)

    class Meta:
        unique_together = [('tenant', 'name')]

    def public(self):
        return {'id': self.id, 'name': self.name, 'title': self.title, 'enabled': self.enabled, 'tenant_id': self.tenant_id}


class TrackEvent(models.Model):
    tenant = models.ForeignKey('accounts.Tenant', null=True, blank=True, on_delete=models.CASCADE, related_name='events')
    account = models.ForeignKey('accounts.Account', null=True, blank=True, on_delete=models.SET_NULL)
    name = models.CharField(max_length=64)
    page = models.CharField(max_length=128, blank=True, default='')
    props = models.JSONField(default=dict, blank=True)
    device = models.CharField(max_length=64, blank=True, default='')
    os_name = models.CharField(max_length=64, blank=True, default='')
    browser = models.CharField(max_length=64, blank=True, default='')
    network = models.CharField(max_length=32, blank=True, default='')
    ip = models.CharField(max_length=64, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-id']

    def public(self):
        return {
            'id': self.id,
            'username': self.account.username if self.account_id else '',
            'name': self.name,
            'page': self.page,
            'props': self.props or {},
            'device': self.device,
            'os_name': self.os_name,
            'browser': self.browser,
            'network': self.network,
            'ip': self.ip,
            'created_at': fmt(self.created_at),
        }


class ClientError(models.Model):
    account = models.ForeignKey('accounts.Account', null=True, blank=True, on_delete=models.SET_NULL)
    kind = models.CharField(max_length=32, default='js')
    message = models.CharField(max_length=500)
    page = models.CharField(max_length=255, blank=True, default='')
    detail = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-id']

    def public(self):
        return {
            'id': self.id,
            'kind': self.kind,
            'message': self.message,
            'page': self.page,
            'detail': self.detail,
            'created_at': fmt(self.created_at),
        }


class IpBlacklist(models.Model):
    ip = models.CharField(max_length=64, unique=True)
    reason = models.CharField(max_length=200, blank=True, default='')
    enabled = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def public(self):
        return {'id': self.id, 'ip': self.ip, 'reason': self.reason, 'enabled': self.enabled, 'created_at': fmt(self.created_at)}
