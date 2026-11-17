import re

from common.response import err

SECRET_KEYS = ('password', 'secret', 'token', 'key')


def password_ok(raw):
    text = raw or ''
    if len(text) < 8:
        return False
    return bool(re.search(r'[A-Za-z]', text) and re.search(r'\d', text))


def current_tenant_id(request):
    account = getattr(request, 'account', None)
    if account is None:
        return None
    if account.is_super and not account.tenant_id:
        raw = request.headers.get('X-Tenant-Id') or request.GET.get('tenant_id') or ''
        if str(raw).isdigit():
            return int(raw)
        return None
    return account.tenant_id


def sees_all(request):
    account = getattr(request, 'account', None)
    return bool(account and account.is_super and not account.tenant_id and current_tenant_id(request) is None)


def tenant_qs(request, qs, field='tenant_id'):
    if sees_all(request):
        return qs
    tenant_id = current_tenant_id(request)
    if not tenant_id:
        return qs.none()
    return qs.filter(**{field: tenant_id})


def stamp_tenant(request, instance):
    tenant_id = current_tenant_id(request)
    if tenant_id and hasattr(instance, 'tenant_id') and not instance.tenant_id:
        instance.tenant_id = tenant_id
    return instance


def module_open(key, default='yes'):
    from common.settings_store import setting
    return setting(key, default) != 'no'


def require_module(key):
    if module_open(key):
        return None
    return err('功能已关闭', 403, 403)


def mask_setting_value(key, value):
    lowered = (key or '').lower()
    if any(word in lowered for word in SECRET_KEYS):
        return '已修改' if value else ''
    return value
