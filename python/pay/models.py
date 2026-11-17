from django.db import models

from common.models import TimeStampedModel
from system.models import fmt


class PayOrder(TimeStampedModel):
    tenant = models.ForeignKey('accounts.Tenant', null=True, blank=True, on_delete=models.CASCADE, related_name='orders')
    order_no = models.CharField(max_length=32, unique=True)
    account = models.ForeignKey('accounts.Account', on_delete=models.CASCADE, related_name='orders')
    subject = models.CharField(max_length=120)
    amount = models.IntegerField(default=0)
    channel = models.CharField(max_length=16, default='mock')
    status = models.CharField(max_length=16, default='pending')
    idempotency_key = models.CharField(max_length=64, blank=True, default='', db_index=True)
    expire_at = models.DateTimeField()
    paid_at = models.DateTimeField(null=True, blank=True)
    remark = models.CharField(max_length=200, blank=True, default='')

    class Meta:
        ordering = ['-id']

    def public(self):
        return {
            'order_no': self.order_no,
            'subject': self.subject,
            'amount': self.amount,
            'channel': self.channel,
            'status': self.status,
            'remark': self.remark,
            'expire_at': fmt(self.expire_at),
            'paid_at': fmt(self.paid_at),
            'created_at': fmt(self.created_at),
        }


class PayCallbackLog(models.Model):
    order = models.ForeignKey(PayOrder, null=True, blank=True, on_delete=models.SET_NULL, related_name='callbacks')
    channel = models.CharField(max_length=16, default='mock')
    payload = models.TextField(blank=True, default='')
    success = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-id']

    def public(self):
        return {
            'id': self.id,
            'order_no': self.order.order_no if self.order_id else '',
            'channel': self.channel,
            'success': self.success,
            'created_at': fmt(self.created_at),
        }
