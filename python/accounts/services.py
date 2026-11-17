import random
from datetime import timedelta

from django.contrib.auth.hashers import check_password, make_password
from django.core.cache import cache
from django.utils import timezone

from accounts.models import Account, Session, SmsCode
from common.auth import account_permissions, apply_refresh_cookie, issue_session
from common.response import ok
from common.security import hash_text
from notify.providers import send_sms
from rbac.models import Menu
from rbac.tree import menu_tree


def auth_response(account, request, remember=False, msg='登录成功'):
    session = issue_session(account, request, remember=remember)
    if account.is_super:
        menus = Menu.objects.all()
    else:
        menus = Menu.objects.filter(roles__in=account.roles.filter(is_deleted=False)).distinct()
    scope = 'platform' if account.is_super and not account.tenant_id else 'tenant'
    response = ok({
        'access_token': session.access_token,
        'account': account.public(mask=True),
        'permissions': account_permissions(account),
        'menus': menu_tree(menus),
        'tenant': account.tenant.public() if account.tenant_id else None,
        'scope': scope,
    }, msg)
    return apply_refresh_cookie(response, session)


def ensure_role(account, code):
    from rbac.models import Role
    role = Role.objects.filter(code=code, is_deleted=False).first()
    if role and not account.roles.filter(id=role.id).exists():
        account.roles.add(role)


def issue_sms(phone, purpose='login'):
    if not cache.add(f'sms-gap:{phone}', 1, 60):
        return None, '发送过于频繁'
    code = f'{random.randint(0, 999999):06d}'
    SmsCode.objects.filter(phone=phone, purpose=purpose, used=False).update(used=True)
    SmsCode.objects.create(
        phone=phone,
        code_hash=hash_text(code),
        purpose=purpose,
        expires_at=timezone.now() + timedelta(minutes=5),
    )
    send_sms(phone, f'验证码 {code}')
    return code, ''


def verify_sms(phone, code, purpose='login'):
    row = SmsCode.objects.filter(phone=phone, purpose=purpose, used=False, expires_at__gte=timezone.now()).order_by('-id').first()
    if row is None or row.code_hash != hash_text(code or ''):
        return False
    row.used = True
    row.save(update_fields=['used'])
    return True


def set_password(account, raw):
    account.password = make_password(raw)
    account.save(update_fields=['password', 'updated_at'])


def check_login_password(account, raw):
    if not account.password:
        return False
    return check_password(raw, account.password)


def revoke_all(account):
    Session.objects.filter(account=account, revoked=False).update(revoked=True)
