import time
from functools import wraps

from django.utils import timezone

from common.response import err

_SEEN = {}


def account_permissions(account):
    if account is None:
        return []
    if account.is_super:
        from rbac.models import Menu
        return list(Menu.objects.exclude(permission='').values_list('permission', flat=True).distinct())
    codes = set()
    roles = account.roles.filter(is_deleted=False).prefetch_related('menus')
    for role in roles:
        for menu in role.menus.all():
            if menu.permission:
                codes.add(menu.permission)
    return sorted(codes)


def has_permission(account, code):
    if account is None:
        return False
    if account.is_super:
        return True
    return code in account_permissions(account)


def login_required(view):
    @wraps(view)
    def wrapper(request, *args, **kwargs):
        account = getattr(request, 'account', None)
        if account is None or account.is_deleted or account.status != 'active':
            return err('未登录或登录已失效', 401, 401)
        return view(request, *args, **kwargs)

    return wrapper


def permission_required(code):
    def deco(view):
        @wraps(view)
        @login_required
        def wrapper(request, *args, **kwargs):
            if not has_permission(request.account, code):
                return err('没有权限', 403, 403)
            return view(request, *args, **kwargs)

        return wrapper

    return deco


def idempotent(view):
    @wraps(view)
    def wrapper(request, *args, **kwargs):
        key = request.headers.get('Idempotency-Key', '').strip()
        if key:
            now = time.time()
            hit = _SEEN.get(key)
            if hit and now - hit < 60:
                return err('请勿重复提交', 409, 409)
            _SEEN[key] = now
            if len(_SEEN) > 500:
                for item in list(_SEEN)[:200]:
                    _SEEN.pop(item, None)
        return view(request, *args, **kwargs)

    return wrapper


def issue_session(account, request, remember=False):
    from django.conf import settings as dj_settings

    from accounts.models import Session
    from common.response import client_ip
    from common.settings_store import setting

    if setting('allow_multi_login', 'yes') != 'yes':
        Session.objects.filter(account=account, revoked=False).update(revoked=True)
    access_minutes = int(setting('access_minutes', '120') or 120)
    refresh_days = int(setting('refresh_days', '30' if remember else '7') or 7)
    now = timezone.now()
    session = Session.objects.create(
        account=account,
        ip=client_ip(request)[:64],
        user_agent=(request.META.get('HTTP_USER_AGENT') or '')[:255],
        access_expires=now + timezone.timedelta(minutes=access_minutes),
        refresh_expires=now + timezone.timedelta(days=refresh_days),
    )
    return session


def apply_refresh_cookie(response, session):
    from django.conf import settings as dj_settings
    response.set_cookie(
        dj_settings.REFRESH_COOKIE,
        session.refresh_token,
        httponly=True,
        samesite='Lax',
        secure=not dj_settings.DEBUG,
        path='/api/v1/auth/',
        max_age=60 * 60 * 24 * 30,
    )
    return response


def clear_refresh_cookie(response):
    from django.conf import settings as dj_settings
    response.delete_cookie(dj_settings.REFRESH_COOKIE, path='/api/v1/auth/')
    return response


def touch_session(token):
    from accounts.models import Session
    if not token:
        return None
    now = timezone.now()
    session = Session.objects.select_related('account').filter(access_token=token, revoked=False).first()
    if session is None or session.access_expires <= now:
        return None
    account = session.account
    if account.is_deleted or account.status != 'active':
        return None
    return session
