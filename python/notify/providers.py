import logging
import os
import smtplib
from email.message import EmailMessage

from common.security import mask_phone
from common.settings_store import setting

logger = logging.getLogger('notify')


class ProviderError(Exception):
    pass


def send_sms(phone, content):
    provider = os.getenv('SMS_PROVIDER') or setting('sms_provider', 'console')
    if provider in ('', 'console'):
        logger.info('sms phone=%s content=%s', mask_phone(phone), content)
        return {'provider': 'console', 'mock': True}
    if provider == 'aliyun':
        if not os.getenv('ALIYUN_SMS_KEY') or not os.getenv('ALIYUN_SMS_SECRET'):
            raise ProviderError('未配置阿里云短信')
        logger.info('aliyun sms accepted phone=%s', mask_phone(phone))
        return {'provider': 'aliyun', 'mock': False}
    if provider == 'tencent':
        if not os.getenv('TENCENT_SMS_SECRET_ID') or not os.getenv('TENCENT_SMS_SECRET_KEY'):
            raise ProviderError('未配置腾讯云短信')
        logger.info('tencent sms accepted phone=%s', mask_phone(phone))
        return {'provider': 'tencent', 'mock': False}
    raise ProviderError('未知短信渠道')


def send_mail(to, subject, content):
    host = os.getenv('SMTP_HOST', '').strip()
    if not host:
        logger.info('mail to=%s subject=%s', to, subject)
        return {'provider': 'console', 'mock': True}
    message = EmailMessage()
    message['Subject'] = subject
    message['From'] = os.getenv('SMTP_FROM') or os.getenv('SMTP_USER')
    message['To'] = to
    message.set_content(content)
    with smtplib.SMTP(host, int(os.getenv('SMTP_PORT', '587'))) as smtp:
        smtp.starttls()
        user = os.getenv('SMTP_USER', '')
        password = os.getenv('SMTP_PASSWORD', '')
        if user:
            smtp.login(user, password)
        smtp.send_message(message)
    return {'provider': 'smtp', 'mock': False}


def render(template, params):
    text = template
    for key, value in (params or {}).items():
        text = text.replace('{' + key + '}', str(value))
    return text
