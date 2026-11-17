import logging
from datetime import timedelta

from django.utils import timezone

logger = logging.getLogger('jobs')


def run_due():
    now = timezone.now()
    from accounts.models import SmsCode
    from pay.models import PayOrder
    from system.models import ApiLog
    from common.settings_store import setting_int

    sms_deleted, _ = SmsCode.objects.filter(expires_at__lt=now).delete()
    closed = PayOrder.objects.filter(status='pending', expire_at__lt=now).update(status='closed')
    keep_days = setting_int('log_keep_days', 30)
    old = now - timedelta(days=keep_days)
    logs_deleted, _ = ApiLog.objects.filter(created_at__lt=old).delete()
    if sms_deleted or closed or logs_deleted:
        logger.info('cleanup sms=%s orders=%s logs=%s', sms_deleted, closed, logs_deleted)
    from notify.models import MessageSendLog
    from notify.providers import send_sms
    for row in MessageSendLog.objects.filter(success=False, channel='sms', retries__lt=3)[:20]:
        try:
            send_sms(row.target, row.content)
            row.success = True
            row.error = ''
        except Exception as exc:
            row.retries += 1
            row.error = str(exc)[:200]
        row.save()
