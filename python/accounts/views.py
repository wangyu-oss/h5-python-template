import secrets
from datetime import timedelta

from django.conf import settings
from django.core.cache import cache
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from accounts.models import Account, Department, Draft, Session, UserGroup, WechatBind
from accounts.services import auth_response, check_login_password, ensure_role, issue_sms, revoke_all, set_password, verify_sms
from accounts.wechat import ProviderError, jsconfig, mini_login, official_login
from common.audit import log_login, log_op
from common.auth import login_required, permission_required
from common.response import body, client_ip, err, ok, paginate
from common.settings_store import setting, setting_int


def _captcha_required(data, account):
    if setting('login_captcha', 'no') == 'yes':
        return True
    return data.get('client') == 'admin' and setting('admin_login_captcha', 'yes') == 'yes' and bool(account and account.failed_logins > 0)


def _captcha_ok(data):
    captcha_id = (data.get('captcha_id') or '').strip()
    answer = str(data.get('captcha_answer') or '').strip()
    expected = cache.get(f'captcha:{captcha_id}')
    cache.delete(f'captcha:{captcha_id}')
    if not expected or answer != str(expected):
        return False, '验证码错误'
    return True, ''


def _lock_message(account):
    if account.locked_until and account.locked_until > timezone.now():
        return '账号已锁定，请稍后再试'
    return ''


@csrf_exempt
@require_http_methods(['GET'])
def captcha(request):
    left = secrets.randbelow(9) + 1
    right = secrets.randbelow(9) + 1
    captcha_id = secrets.token_hex(8)
    cache.set(f'captcha:{captcha_id}', left + right, 300)
    return ok({'captcha_id': captcha_id, 'question': f'{left} + {right} = ?'})


@csrf_exempt
@require_http_methods(['POST'])
def login(request):
    data = body(request)
    if data is None:
        return err('参数错误')
    username = (data.get('username') or '').strip()
    password = data.get('password') or ''
    account = Account.objects.filter(username=username, is_deleted=False).first()
    if _captcha_required(data, account):
        passed, message = _captcha_ok(data)
        if not passed:
            return err(message, data={'captcha': True})
    if account is None or account.status != 'active':
        log_login(username, False, '账号或密码错误', request)
        return err('账号或密码错误')
    locked = _lock_message(account)
    if locked:
        return err(locked)
    if not check_login_password(account, password):
        account.failed_logins += 1
        if account.failed_logins >= setting_int('login_fail_limit', 5):
            account.locked_until = timezone.now() + timedelta(minutes=setting_int('login_lock_minutes', 10))
        account.save(update_fields=['failed_logins', 'locked_until', 'updated_at'])
        log_login(username, False, '账号或密码错误', request)
        need_captcha = data.get('client') == 'admin' and setting('admin_login_captcha', 'yes') == 'yes'
        return err('账号或密码错误', data={'captcha': need_captcha})
    previous_ip = account.last_login_ip
    ip = client_ip(request)[:64]
    account.failed_logins = 0
    account.locked_until = None
    account.last_login_ip = ip
    account.save(update_fields=['failed_logins', 'locked_until', 'last_login_ip', 'updated_at'])
    log_login(username, True, '登录成功', request, account.tenant_id)
    if previous_ip and previous_ip != ip:
        from notify.models import InboxMessage
        InboxMessage.objects.create(tenant_id=account.tenant_id, account=account, category='security', title='登录提醒', content=f'账号在新的 IP {ip} 登录')
    return auth_response(account, request, remember=bool(data.get('remember')))


@csrf_exempt
@require_http_methods(['POST'])
def sms_send(request):
    data = body(request) or {}
    phone = (data.get('phone') or '').strip()
    purpose = (data.get('purpose') or 'login').strip()
    if len(phone) < 6:
        return err('手机号不正确')
    code, message = issue_sms(phone, purpose)
    if not code:
        return err(message)
    payload = {'sent': True}
    if settings.DEBUG or setting('sms_provider', 'console') == 'console':
        payload['debug_code'] = code
    return ok(payload, '验证码已发送')


@csrf_exempt
@require_http_methods(['POST'])
def sms_login(request):
    data = body(request) or {}
    phone = (data.get('phone') or '').strip()
    if not verify_sms(phone, data.get('code') or '', 'login'):
        log_login(phone, False, '验证码错误', request)
        return err('验证码错误')
    account = Account.objects.filter(phone=phone, is_deleted=False).exclude(status='cancelled').first()
    if account is None:
        account = Account.objects.create(username=phone, phone=phone, display_name=f'用户{phone[-4:]}', status='active')
        ensure_role(account, 'user')
    if account.status != 'active':
        return err('账号不可用')
    log_login(account.username, True, '验证码登录', request)
    return auth_response(account, request, remember=True)


@csrf_exempt
@require_http_methods(['POST'])
def guest_login(request):
    data = body(request) or {}
    device = (data.get('device_id') or request.headers.get('X-Device-Id') or 'device').strip()[:40]
    username = f'guest_{device}'
    account = Account.objects.filter(username=username).first()
    if account is None:
        account = Account.objects.create(username=username, display_name='游客', is_guest=True, status='active')
        ensure_role(account, 'guest')
    log_login(username, True, '游客', request)
    return auth_response(account, request, msg='游客登录成功')


def _wechat_account(profile, platform):
    bind = WechatBind.objects.select_related('account').filter(platform=platform, openid=profile['openid']).first()
    if bind:
        return bind.account
    account = Account.objects.create(
        username=f'{platform}_{profile["openid"]}'[:64],
        display_name=profile.get('nickname') or '微信用户',
        status='active',
    )
    ensure_role(account, 'user')
    WechatBind.objects.create(account=account, platform=platform, openid=profile['openid'], unionid=profile.get('unionid') or '')
    return account


@csrf_exempt
@require_http_methods(['POST'])
def wechat_official(request):
    data = body(request) or {}
    try:
        profile = official_login((data.get('code') or '').strip())
    except ProviderError as exc:
        return err(str(exc))
    account = _wechat_account(profile, 'official')
    log_login(account.username, True, '微信公众号', request)
    response = auth_response(account, request)
    return response


@csrf_exempt
@require_http_methods(['POST'])
def wechat_mini(request):
    data = body(request) or {}
    try:
        profile = mini_login((data.get('code') or '').strip())
    except ProviderError as exc:
        return err(str(exc))
    account = _wechat_account(profile, 'mini')
    log_login(account.username, True, '微信小程序', request)
    return auth_response(account, request)


@csrf_exempt
@require_http_methods(['POST'])
def oneclick(request):
    return err('未配置运营商一键登录')


@csrf_exempt
@require_http_methods(['POST'])
def refresh(request):
    token = request.COOKIES.get(settings.REFRESH_COOKIE, '')
    session = Session.objects.select_related('account').filter(refresh_token=token, revoked=False).first()
    now = timezone.now()
    if session is None or session.refresh_expires <= now or session.account.status != 'active':
        return err('登录已失效', 401, 401)
    minutes = setting_int('access_minutes', 120)
    session.access_token = secrets.token_hex(32)
    session.refresh_token = secrets.token_hex(32)
    session.access_expires = now + timedelta(minutes=minutes)
    session.save(update_fields=['access_token', 'refresh_token', 'access_expires'])
    return auth_response_from_session(session)


def auth_response_from_session(session):
    from common.auth import account_permissions, apply_refresh_cookie
    from rbac.models import Menu
    from rbac.tree import menu_tree
    account = session.account
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
    })
    return apply_refresh_cookie(response, session)


@csrf_exempt
@require_http_methods(['POST'])
def logout(request):
    if request.session_row is not None:
        request.session_row.revoked = True
        request.session_row.save(update_fields=['revoked'])
    token = request.COOKIES.get(settings.REFRESH_COOKIE, '')
    if token:
        Session.objects.filter(refresh_token=token).update(revoked=True)
    from common.auth import clear_refresh_cookie
    return clear_refresh_cookie(ok({'ok': True}, '已退出'))


@csrf_exempt
@require_http_methods(['POST'])
def register(request):
    if setting('register_enabled', 'yes') != 'yes':
        return err('未开放注册')
    data = body(request) or {}
    username = (data.get('username') or '').strip()
    password = data.get('password') or ''
    from common.scope import password_ok
    if len(username) < 3 or not password_ok(password):
        return err('用户名至少 3 位，密码至少 8 位且包含字母和数字')
    if Account.objects.filter(username=username).exists():
        return err('用户名已存在')
    account = Account.objects.create(username=username, display_name=username, phone=(data.get('phone') or '')[:32], status='active')
    set_password(account, password)
    ensure_role(account, 'user')
    log_op(request, 'register', username)
    return auth_response(account, request, msg='注册成功')


@csrf_exempt
@require_http_methods(['POST'])
def password_reset(request):
    data = body(request) or {}
    phone = (data.get('phone') or '').strip()
    if not verify_sms(phone, data.get('code') or '', 'reset'):
        return err('验证码错误')
    account = Account.objects.filter(phone=phone, is_deleted=False).first()
    if account is None:
        return err('手机号未注册')
    from common.scope import password_ok
    password = data.get('password') or ''
    if not password_ok(password):
        return err('密码至少 8 位且包含字母和数字')
    set_password(account, password)
    revoke_all(account)
    return ok({'reset': True}, '密码已重置')


@csrf_exempt
@login_required
@require_http_methods(['POST'])
def password_change(request):
    data = body(request) or {}
    if not check_login_password(request.account, data.get('old_password') or ''):
        return err('原密码错误')
    from common.scope import password_ok
    password = data.get('password') or ''
    if not password_ok(password):
        return err('密码至少 8 位且包含字母和数字')
    set_password(request.account, password)
    return ok({'changed': True})


@csrf_exempt
@login_required
@require_http_methods(['POST'])
def cancel_account(request):
    request.account.status = 'cancelled'
    request.account.save(update_fields=['status', 'updated_at'])
    revoke_all(request.account)
    log_op(request, 'cancel', request.account.username)
    return ok({'cancelled': True})


@csrf_exempt
@login_required
@require_http_methods(['GET'])
def me(request):
    from common.auth import account_permissions
    from rbac.models import Menu
    from rbac.tree import menu_tree
    account = request.account
    client = request.GET.get('client') or ''
    if account.is_super:
        menus = Menu.objects.all()
    else:
        menus = Menu.objects.filter(roles__in=account.roles.filter(is_deleted=False)).distinct()
    if client:
        menus = menus.filter(client=client)
    menus = _with_ancestors(list(menus))
    scope = 'platform' if account.is_super and not account.tenant_id else 'tenant'
    return ok({
        'account': account.public(mask=not account.is_super),
        'permissions': account_permissions(account),
        'menus': menu_tree(menus),
        'tenant': account.tenant.public() if account.tenant_id else None,
        'scope': scope,
    })


@csrf_exempt
@login_required
@require_http_methods(['POST'])
def profile(request):
    data = body(request) or {}
    account = request.account
    for field in ('display_name', 'avatar', 'gender', 'email'):
        if field in data:
            setattr(account, field, str(data.get(field) or '')[:128])
    if data.get('birthday'):
        account.birthday = data.get('birthday')
    if 'tags' in data and isinstance(data['tags'], list):
        account.tags = [str(item)[:20] for item in data['tags'][:20]]
    account.save()
    return ok(account.public())


@csrf_exempt
@login_required
@require_http_methods(['POST'])
def realname(request):
    data = body(request) or {}
    name = (data.get('real_name') or '').strip()
    id_card = (data.get('id_card') or '').strip()
    if len(name) < 2 or len(id_card) < 8:
        return err('请填写姓名和证件号')
    request.account.real_name = name[:64]
    request.account.id_card = id_card[:32]
    request.account.realname_status = 'mock'
    request.account.save(update_fields=['real_name', 'id_card', 'realname_status', 'updated_at'])
    return ok(request.account.public(), '已按模拟渠道完成实名')


@csrf_exempt
@login_required
@require_http_methods(['GET', 'POST'])
def drafts(request):
    if request.method == 'GET':
        key = (request.GET.get('key') or '').strip()
        row = Draft.objects.filter(account=request.account, key=key).first()
        return ok({'key': key, 'content': row.content if row else ''})
    data = body(request) or {}
    key = (data.get('key') or '').strip()[:64]
    if not key:
        return err('缺少草稿键')
    Draft.objects.update_or_create(account=request.account, key=key, defaults={'content': data.get('content') or ''})
    return ok({'saved': True})


@csrf_exempt
@require_http_methods(['POST'])
def wechat_jsconfig(request):
    data = body(request) or {}
    url = (data.get('url') or '').split('#')[0]
    try:
        return ok(jsconfig(url))
    except Exception as exc:
        return err(f'微信签名失败: {exc}')


def _scoped_users(request):
    from common.scope import tenant_qs
    qs = tenant_qs(request, Account.objects.filter(is_deleted=False).select_related('dept', 'tenant'))
    account = request.account
    if account.is_super:
        return qs
    role = account.roles.filter(is_deleted=False).first()
    scope = role.data_scope if role else 'self'
    if scope == 'all':
        return qs
    if scope == 'dept' and account.dept_id:
        return qs.filter(dept_id=account.dept_id)
    return qs.filter(id=account.id)


@csrf_exempt
@permission_required('admin:user:list')
@require_http_methods(['GET'])
def users(request):
    qs = _scoped_users(request).prefetch_related('roles')
    from django.db.models import Q
    keyword = (request.GET.get('keyword') or '').strip()
    status = (request.GET.get('status') or '').strip()
    if keyword:
        qs = qs.filter(Q(username__icontains=keyword) | Q(display_name__icontains=keyword) | Q(phone__icontains=keyword))
    if status:
        qs = qs.filter(status=status)
    total, rows = paginate(request, qs)
    items = []
    for row in rows:
        item = row.public(mask=True)
        item['role_names'] = [role.name for role in row.roles.all() if not role.is_deleted]
        items.append(item)
    return ok({'items': items, 'total': total})


@csrf_exempt
@permission_required('admin:user:save')
@require_http_methods(['POST'])
def user_save(request):
    data = body(request) or {}
    account_id = data.get('id')
    if account_id:
        account = Account.objects.filter(id=account_id, is_deleted=False).first()
        if account is None:
            return err('用户不存在')
    else:
        username = (data.get('username') or '').strip()
        if not username:
            return err('请填写用户名')
        account = Account(username=username, status='active')
        from common.scope import current_tenant_id
        account.tenant_id = current_tenant_id(request)
    owned = _scoped_users(request).filter(id=account.id).exists() if account_id else True
    if account_id and not owned:
        return err('没有权限', 403, 403)
    for field in ('display_name', 'phone', 'email', 'avatar', 'gender', 'status'):
        if field in data:
            setattr(account, field, str(data.get(field) or '')[:128])
    if 'dept_id' in data:
        account.dept_id = data.get('dept_id') or None
    if data.get('password'):
        from common.scope import password_ok
        if not password_ok(data['password']):
            return err('密码至少 8 位且包含字母和数字')
        account.password = ''
        account.save()
        set_password(account, data['password'])
    else:
        account.save()
    if 'role_ids' in data:
        account.roles.set(data.get('role_ids') or [])
    if 'group_ids' in data:
        account.groups.set(data.get('group_ids') or [])
    if 'tags' in data and isinstance(data['tags'], list):
        account.tags = data['tags']
        account.save(update_fields=['tags'])
    log_op(request, 'user_save', account.username)
    return ok(account.public(mask=False))


@csrf_exempt
@permission_required('admin:user:save')
@require_http_methods(['POST'])
def user_delete(request):
    data = body(request) or {}
    account = Account.objects.filter(id=data.get('id'), is_deleted=False).first()
    if account is None:
        return err('用户不存在')
    if account.is_super:
        return err('不能删除超级管理员')
    account.soft_delete()
    revoke_all(account)
    log_op(request, 'user_delete', account.username)
    return ok({'deleted': True})


@csrf_exempt
@permission_required('admin:user:save')
@require_http_methods(['POST'])
def user_status(request):
    data = body(request) or {}
    raw_ids = data.get('ids') if isinstance(data.get('ids'), list) else []
    if data.get('id'):
        raw_ids.append(data.get('id'))
    ids = [item for item in raw_ids if str(item).isdigit() or isinstance(item, int)]
    accounts = list(_scoped_users(request).filter(id__in=ids))
    if not accounts:
        return err('用户不存在')
    status = 'disabled' if data.get('status') == 'disabled' else 'active'
    for account in accounts:
        account.status = status
        account.save(update_fields=['status', 'updated_at'])
        if status != 'active':
            revoke_all(account)
        log_op(request, 'user_status', account.username, status)
    return ok({'updated': len(accounts)})


@csrf_exempt
@permission_required('admin:user:list')
@require_http_methods(['GET'])
def groups(request):
    return ok({'items': [row.public() for row in UserGroup.objects.filter(is_deleted=False)]})


@csrf_exempt
@permission_required('admin:user:save')
@require_http_methods(['POST'])
def group_save(request):
    data = body(request) or {}
    if data.get('id'):
        row = UserGroup.objects.filter(id=data['id']).first()
    else:
        row = UserGroup(code=(data.get('code') or '').strip())
    row.name = (data.get('name') or row.name or '')[:64]
    if data.get('code'):
        row.code = data['code'][:64]
    row.save()
    return ok(row.public())


@csrf_exempt
@permission_required('admin:user:list')
@require_http_methods(['GET'])
def depts(request):
    return ok({'items': [row.public() for row in Department.objects.filter(is_deleted=False)]})


@csrf_exempt
@login_required
@require_http_methods(['GET'])
def online(request):
    now = timezone.now()
    rows = Session.objects.select_related('account').filter(revoked=False, access_expires__gt=now)
    if request.GET.get('mine') == '1':
        rows = rows.filter(account=request.account)
    elif not request.account.is_super and not _has(request, 'admin:user:list'):
        return err('没有权限', 403, 403)
    return ok({'items': [{
        'id': row.id,
        'username': row.account.username,
        'ip': row.ip,
        'user_agent': row.user_agent,
        'created_at': timezone.localtime(row.created_at).strftime('%Y-%m-%d %H:%M:%S'),
    } for row in rows[:200]]})


@csrf_exempt
@permission_required('admin:user:save')
@require_http_methods(['POST'])
def online_kick(request):
    data = body(request) or {}
    Session.objects.filter(id=data.get('id')).update(revoked=True)
    return ok({'kicked': True})


def _has(request, code):
    from common.auth import has_permission
    return has_permission(request.account, code)


def _with_ancestors(menus):
    from rbac.models import Menu
    rows = list(menus)
    seen = {row.id for row in rows}
    pending = [row.parent_id for row in rows if row.parent_id and row.parent_id not in seen]
    while pending:
        extra = list(Menu.objects.filter(id__in=pending))
        pending = []
        for row in extra:
            if row.id in seen:
                continue
            rows.append(row)
            seen.add(row.id)
            if row.parent_id and row.parent_id not in seen:
                pending.append(row.parent_id)
    return rows


@csrf_exempt
@permission_required('admin:user:list')
@require_http_methods(['GET'])
def user_detail(request, user_id):
    account = _scoped_users(request).filter(id=user_id).first()
    if account is None:
        return err('用户不存在', 404, 404)
    from system.models import LoginLog
    from track.models import TrackEvent
    events = TrackEvent.objects.filter(account=account).order_by('-id')[:20]
    logs = LoginLog.objects.filter(username=account.username).order_by('-id')[:20]
    data = account.public(mask=True)
    data['roles'] = [{'id': role.id, 'name': role.name} for role in account.roles.filter(is_deleted=False)]
    data['events'] = [row.public() for row in events]
    data['login_logs'] = [row.public() for row in logs]
    return ok(data)


@csrf_exempt
@permission_required('admin:export')
@require_http_methods(['GET'])
def users_export(request):
    from io import BytesIO
    from django.http import HttpResponse
    from openpyxl import Workbook
    book = Workbook()
    sheet = book.active
    sheet.append(['username', 'display_name', 'phone', 'status', 'tenant'])
    for account in _scoped_users(request)[:1000]:
        item = account.public(mask=True)
        sheet.append([item['username'], item['display_name'], item['phone'], item['status'], item['tenant_name']])
    buffer = BytesIO()
    book.save(buffer)
    response = HttpResponse(buffer.getvalue(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="users.xlsx"'
    return response


@csrf_exempt
@permission_required('admin:user:save')
@require_http_methods(['POST'])
def users_import(request):
    from openpyxl import load_workbook
    from common.scope import current_tenant_id, password_ok
    upload = request.FILES.get('file')
    if upload is None:
        return err('请上传文件')
    book = load_workbook(upload, read_only=True)
    created = 0
    for index, row in enumerate(book.active.iter_rows(values_only=True)):
        if index == 0 or not row or not row[0]:
            continue
        username = str(row[0]).strip()
        if Account.objects.filter(username=username).exists():
            continue
        password = str(row[3] or 'Local#8k2p')
        if not password_ok(password):
            password = 'Local#8k2p'
        account = Account(username=username, display_name=str(row[1] or username)[:64], phone=str(row[2] or '')[:32], status='active')
        account.tenant_id = current_tenant_id(request)
        account.save()
        set_password(account, password)
        ensure_role(account, 'user')
        created += 1
    return ok({'created': created})


@csrf_exempt
@permission_required('admin:tenant')
@require_http_methods(['GET'])
def tenants(request):
    from accounts.models import Tenant
    rows = Tenant.objects.filter(is_deleted=False)
    return ok({'items': [row.public() for row in rows]})


@csrf_exempt
@permission_required('admin:tenant')
@require_http_methods(['POST'])
def tenant_save(request):
    from accounts.models import Tenant
    data = body(request) or {}
    if data.get('id'):
        row = Tenant.objects.filter(id=data['id'], is_deleted=False).first()
        if row is None:
            return err('客户不存在')
    else:
        code = (data.get('code') or '').strip()
        if not code:
            return err('请填写客户编码')
        row = Tenant(code=code)
    row.name = (data.get('name') or row.name or row.code)[:64]
    if data.get('code'):
        row.code = data['code'][:64]
    row.status = data.get('status') or row.status or 'active'
    if data.get('expire_at'):
        row.expire_at = data['expire_at']
    row.save()
    log_op(request, 'tenant_save', row.code)
    return ok(row.public())


@csrf_exempt
@permission_required('admin:tenant')
@require_http_methods(['POST'])
def tenant_status(request):
    from accounts.models import Tenant
    data = body(request) or {}
    row = Tenant.objects.filter(id=data.get('id'), is_deleted=False).first()
    if row is None:
        return err('客户不存在')
    row.status = 'disabled' if data.get('status') == 'disabled' else 'active'
    row.save(update_fields=['status', 'updated_at'])
    log_op(request, 'tenant_status', row.code, row.status)
    return ok(row.public())
