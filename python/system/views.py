from io import BytesIO

from django.db.models import Q
from django.http import HttpResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from openpyxl import Workbook, load_workbook

from accounts.models import Account
from common.audit import log_op
from common.auth import login_required, permission_required
from common.response import body, err, ok, paginate
from common.settings_store import PUBLIC_KEYS, clear_setting_cache
from system.models import Announcement, ApiLog, Banner, DictItem, DictType, LoginLog, OperationLog, Region, Setting, SettingChange


def module_closed(key):
    from common.scope import module_open
    return not module_open(key)


def _visible(qs):
    now = timezone.now()
    return qs.filter(is_deleted=False, enabled=True).filter(
        Q(start_at__isnull=True) | Q(start_at__lte=now),
        Q(end_at__isnull=True) | Q(end_at__gte=now),
    ).order_by('-pinned', '-id')


def _log_qs(request, qs):
    from common.scope import tenant_qs
    qs = tenant_qs(request, qs)
    keyword = (request.GET.get('keyword') or '').strip()
    start = request.GET.get('start') or ''
    end = request.GET.get('end') or ''
    if keyword and hasattr(qs.model, 'username'):
        qs = qs.filter(username__icontains=keyword)
    elif keyword and hasattr(qs.model, 'path'):
        qs = qs.filter(path__icontains=keyword)
    elif keyword:
        qs = qs.filter(action__icontains=keyword)
    if start:
        qs = qs.filter(created_at__date__gte=start)
    if end:
        qs = qs.filter(created_at__date__lte=end)
    success = request.GET.get('success')
    if success in ('1', '0') and hasattr(qs.model, 'success'):
        qs = qs.filter(success=success == '1')
    return qs


@csrf_exempt
@require_http_methods(['GET'])
def health(request):
    import os
    from django.conf import settings
    return ok({'status': 'up', 'debug': settings.DEBUG, 'db': settings.DB_ENGINE, 'env': os.getenv('APP_ENV', 'dev'), 'version': '1.1.0'})


@csrf_exempt
@require_http_methods(['GET'])
def public_config(request):
    data = {row.key: row.value for row in Setting.objects.filter(key__in=PUBLIC_KEYS, tenant__isnull=True)}
    if module_closed('module_notice'):
        notices = []
    else:
        notices = [row.public() for row in _visible(Announcement.objects.all())[:5]]
    banners = [] if module_closed('module_banner') else [row.public() for row in _visible(Banner.objects.all())]
    return ok({'settings': data, 'banners': banners, 'notices': notices})


@csrf_exempt
@require_http_methods(['GET'])
def banners(request):
    if module_closed('module_banner'):
        return ok({'items': []})
    return ok({'items': [row.public() for row in _visible(Banner.objects.all())]})


@csrf_exempt
@require_http_methods(['GET'])
def announcements(request):
    if module_closed('module_notice'):
        return ok({'items': [], 'total': 0})
    qs = _visible(Announcement.objects.all())
    total, rows = paginate(request, qs)
    return ok({'items': [row.public() for row in rows], 'total': total})


@csrf_exempt
@require_http_methods(['GET'])
def announcement_detail(request, announcement_id):
    row = Announcement.objects.filter(id=announcement_id, is_deleted=False, enabled=True).first()
    if row is None:
        return err('公告不存在', 404, 404)
    return ok(row.public(detail=True))


@csrf_exempt
@require_http_methods(['GET'])
def regions(request):
    rows = [row.public() for row in Region.objects.all()]
    grouped = {}
    for row in rows:
        grouped.setdefault(row['parent_id'], []).append(row)

    def build(parent_id):
        nodes = grouped.get(parent_id, [])
        for node in nodes:
            children = build(node['id'])
            if children:
                node['children'] = children
        return nodes

    return ok({'items': build(None)})


@csrf_exempt
@require_http_methods(['GET'])
def dict_public(request, code):
    dict_type = DictType.objects.filter(code=code, is_deleted=False).first()
    if dict_type is None:
        return err('字典不存在', 404, 404)
    items = dict_type.items.filter(is_deleted=False, enabled=True)
    return ok({'code': code, 'items': [row.public() for row in items]})


@csrf_exempt
@permission_required('admin:setting')
@require_http_methods(['GET'])
def settings_get(request):
    import os
    Setting.objects.get_or_create(
        key='app_env',
        tenant=None,
        defaults={'value': os.getenv('APP_ENV', 'dev'), 'remark': '当前环境，dev 或 prod', 'category': 'basic'},
    )
    return ok({'items': [row.public() for row in Setting.objects.all().order_by('key')]})


@csrf_exempt
@permission_required('admin:setting')
@require_http_methods(['POST'])
def settings_save(request):
    data = body(request) or {}
    items = data.get('items') or []
    if data.get('key'):
        items = [{'key': data.get('key'), 'value': data.get('value', ''), 'remark': data.get('remark', '')}]
    for item in items:
        key = (item.get('key') or '').strip()
        if not key:
            continue
        from common.scope import current_tenant_id, mask_setting_value
        tenant_id = current_tenant_id(request)
        value = str(item.get('value', ''))
        existing = Setting.objects.filter(key=key[:64], tenant_id=tenant_id).first()
        old_value = existing.value if existing else ''
        Setting.objects.update_or_create(
            key=key[:64],
            tenant_id=tenant_id,
            defaults={'value': value, 'remark': (item.get('remark') or '')[:200], 'category': (item.get('category') or 'basic')[:16]},
        )
        SettingChange.objects.create(
            tenant_id=tenant_id,
            account=getattr(request, 'account', None),
            key=key[:64],
            old_value=mask_setting_value(key, old_value),
            new_value=mask_setting_value(key, value),
        )
        clear_setting_cache(key)
    log_op(request, 'settings_save', ','.join(item.get('key', '') for item in items))
    return ok({'saved': True})


@csrf_exempt
@permission_required('admin:banner')
@require_http_methods(['GET'])
def admin_banners(request):
    return ok({'items': [row.public() for row in Banner.objects.filter(is_deleted=False)]})


@csrf_exempt
@permission_required('admin:banner')
@require_http_methods(['POST'])
def banner_save(request):
    data = body(request) or {}
    row = Banner.objects.filter(id=data.get('id'), is_deleted=False).first() if data.get('id') else Banner()
    if row is None:
        return err('轮播不存在')
    row.title = (data.get('title') or '')[:80]
    row.image = (data.get('image') or '')[:255]
    row.link = (data.get('link') or '')[:255]
    row.color = (data.get('color') or '#1989fa')[:16]
    row.sort = int(data.get('sort') or 0)
    row.enabled = bool(data.get('enabled', True))
    row.jump_type = (data.get('jump_type') or 'page')[:16]
    row.pinned = bool(data.get('pinned', False))
    row.start_at = data.get('start_at') or None
    row.end_at = data.get('end_at') or None
    from common.scope import current_tenant_id
    if not row.tenant_id:
        row.tenant_id = current_tenant_id(request)
    row.save()
    log_op(request, 'banner_save', row.title)
    return ok(row.public())


@csrf_exempt
@permission_required('admin:banner')
@require_http_methods(['POST'])
def banner_delete(request):
    data = body(request) or {}
    row = Banner.objects.filter(id=data.get('id'), is_deleted=False).first()
    if row is None:
        return err('轮播不存在')
    row.soft_delete()
    return ok({'deleted': True})


@csrf_exempt
@permission_required('admin:notice')
@require_http_methods(['GET'])
def admin_announcements(request):
    from common.scope import tenant_qs
    qs = tenant_qs(request, Announcement.objects.filter(is_deleted=False))
    keyword = (request.GET.get('keyword') or '').strip()
    enabled = request.GET.get('enabled') or ''
    if keyword:
        qs = qs.filter(title__icontains=keyword)
    if enabled == 'yes':
        qs = qs.filter(enabled=True)
    elif enabled == 'no':
        qs = qs.filter(enabled=False)
    total, rows = paginate(request, qs)
    return ok({'items': [row.public(detail=True) for row in rows], 'total': total})


@csrf_exempt
@permission_required('admin:notice')
@require_http_methods(['POST'])
def announcement_save(request):
    data = body(request) or {}
    row = Announcement.objects.filter(id=data.get('id'), is_deleted=False).first() if data.get('id') else Announcement()
    if row is None:
        return err('公告不存在')
    row.title = (data.get('title') or '')[:120]
    row.content = data.get('content') or ''
    row.enabled = bool(data.get('enabled', True))
    row.jump_type = (data.get('jump_type') or 'none')[:16]
    row.pinned = bool(data.get('pinned', False))
    row.start_at = data.get('start_at') or None
    row.end_at = data.get('end_at') or None
    from common.scope import current_tenant_id
    if not row.tenant_id:
        row.tenant_id = current_tenant_id(request)
    row.save()
    log_op(request, 'announcement_save', row.title)
    return ok(row.public(detail=True))


@csrf_exempt
@permission_required('admin:notice')
@require_http_methods(['POST'])
def announcement_delete(request):
    data = body(request) or {}
    row = Announcement.objects.filter(id=data.get('id'), is_deleted=False).first()
    if row is None:
        return err('公告不存在')
    row.soft_delete()
    return ok({'deleted': True})


@csrf_exempt
@permission_required('admin:dict')
@require_http_methods(['GET'])
def dicts(request):
    types = []
    for row in DictType.objects.filter(is_deleted=False):
        item = row.public()
        item['items'] = [child.public() for child in row.items.filter(is_deleted=False)]
        types.append(item)
    return ok({'items': types})


@csrf_exempt
@permission_required('admin:dict')
@require_http_methods(['POST'])
def dict_save(request):
    data = body(request) or {}
    if data.get('dict_type_id') or data.get('label'):
        dict_type = DictType.objects.filter(id=data.get('dict_type_id')).first()
        if dict_type is None and data.get('code'):
            dict_type, _ = DictType.objects.get_or_create(code=data['code'], defaults={'name': data.get('name') or data['code']})
        if dict_type is None:
            return err('字典不存在')
        if data.get('id'):
            item = DictItem.objects.filter(id=data['id']).first()
        else:
            item = DictItem(dict_type=dict_type)
        item.dict_type = dict_type
        item.label = (data.get('label') or '')[:64]
        item.value = (data.get('value') or '')[:64]
        item.sort = int(data.get('sort') or 0)
        item.enabled = bool(data.get('enabled', True))
        item.save()
        return ok(item.public())
    code = (data.get('code') or '').strip()
    if not code:
        return err('请填写字典编码')
    row, _ = DictType.objects.get_or_create(code=code, defaults={'name': data.get('name') or code})
    row.name = (data.get('name') or row.name)[:64]
    row.save()
    return ok(row.public())


@csrf_exempt
@permission_required('admin:dict')
@require_http_methods(['POST'])
def dict_delete(request):
    data = body(request) or {}
    if data.get('item_id'):
        DictItem.objects.filter(id=data['item_id']).update(is_deleted=True)
    elif data.get('id'):
        DictType.objects.filter(id=data['id']).update(is_deleted=True)
    return ok({'deleted': True})


@csrf_exempt
@permission_required('admin:dict')
@require_http_methods(['GET'])
def admin_regions(request):
    return ok({'items': [row.public() for row in Region.objects.all()]})


@csrf_exempt
@permission_required('admin:dict')
@require_http_methods(['POST'])
def region_save(request):
    data = body(request) or {}
    code = (data.get('code') or '').strip()
    row = Region.objects.filter(code=code).first() if code else None
    if row is None:
        row = Region(code=code)
    row.name = (data.get('name') or '')[:64]
    row.parent_id = data.get('parent_id') or None
    row.save()
    return ok(row.public())


@csrf_exempt
@permission_required('admin:log')
@require_http_methods(['GET'])
def login_logs(request):
    total, rows = paginate(request, _log_qs(request, LoginLog.objects.all()))
    return ok({'items': [row.public() for row in rows], 'total': total})


@csrf_exempt
@permission_required('admin:log')
@require_http_methods(['GET'])
def operation_logs(request):
    total, rows = paginate(request, _log_qs(request, OperationLog.objects.select_related('account')))
    return ok({'items': [row.public() for row in rows], 'total': total})


@csrf_exempt
@permission_required('admin:log')
@require_http_methods(['GET'])
def api_logs(request):
    qs = ApiLog.objects.select_related('account')
    status = request.GET.get('status')
    if status == 'error':
        qs = qs.filter(status_code__gte=400)
    total, rows = paginate(request, qs)
    return ok({'items': [row.public() for row in rows], 'total': total})


@csrf_exempt
@permission_required('admin:log')
@require_http_methods(['GET'])
def dashboard(request):
    from django.db.models import Count
    from django.db.models.functions import TruncDate
    from pay.models import PayOrder
    from track.models import TrackEvent
    from common.scope import tenant_qs
    start = request.GET.get('start') or ''
    end = request.GET.get('end') or ''
    users = tenant_qs(request, Account.objects.filter(is_deleted=False, is_guest=False))
    orders = tenant_qs(request, PayOrder.objects.all())
    events = tenant_qs(request, TrackEvent.objects.all())
    if start:
        orders = orders.filter(created_at__date__gte=start)
        events = events.filter(created_at__date__gte=start)
        users = users.filter(created_at__date__gte=start)
    if end:
        orders = orders.filter(created_at__date__lte=end)
        events = events.filter(created_at__date__lte=end)
        users = users.filter(created_at__date__lte=end)

    def days(qs):
        rows = qs.annotate(day=TruncDate('created_at')).values('day').annotate(total=Count('id')).order_by('day')
        return [{'day': row['day'].isoformat() if row['day'] else '', 'total': row['total']} for row in rows]

    paid = orders.filter(status='paid').count()
    from notify.models import MessageSendLog
    failed_messages = tenant_qs(request, MessageSendLog.objects.filter(success=False)).order_by('-id')[:8]
    failed_logins = tenant_qs(request, LoginLog.objects.filter(success=False)).order_by('-id')[:8]
    return ok({
        'users': users.count(),
        'orders': orders.count(),
        'paid_orders': paid,
        'events': events.count(),
        'pending_orders': orders.filter(status='pending').count(),
        'notices': tenant_qs(request, Announcement.objects.filter(is_deleted=False, enabled=True)).count(),
        'users_by_day': days(users),
        'orders_by_day': days(orders),
        'pay_funnel': [
            {'name': '下单', 'total': orders.count()},
            {'name': '已支付', 'total': paid},
            {'name': '退款', 'total': orders.filter(status__in=['refunding', 'refunded']).count()},
        ],
        'event_names': list(events.values('name').annotate(total=Count('id')).order_by('-total')[:8]),
        'failed_messages': [row.public() for row in failed_messages],
        'failed_logins': [row.public() for row in failed_logins],
    })


def _xlsx(headers, rows, filename):
    book = Workbook()
    sheet = book.active
    sheet.append(headers)
    for row in rows:
        sheet.append(row)
    buffer = BytesIO()
    book.save(buffer)
    response = HttpResponse(buffer.getvalue(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


@csrf_exempt
@permission_required('admin:export')
@require_http_methods(['GET'])
def login_logs_export(request):
    rows = []
    for row in _log_qs(request, LoginLog.objects.all())[:1000]:
        item = row.public()
        rows.append([item.get('username'), item.get('success'), item.get('message'), item.get('ip'), item.get('created_at')])
    return _xlsx(['username', 'success', 'message', 'ip', 'created_at'], rows, 'login-logs.xlsx')


@csrf_exempt
@permission_required('admin:export')
@require_http_methods(['GET'])
def dashboard_export(request):
    payload = dashboard(request)
    import json
    data = json.loads(payload.content.decode('utf-8')).get('data') or {}
    rows = [[item['day'], item['total']] for item in data.get('users_by_day') or []]
    return _xlsx(['day', 'users'], rows, 'dashboard.xlsx')


@csrf_exempt
@login_required
@require_http_methods(['GET'])
def excel_export(request):
    book = Workbook()
    sheet = book.active
    sheet.title = 'users'
    sheet.append(['username', 'display_name', 'phone', 'status'])
    for account in Account.objects.filter(is_deleted=False, is_guest=False)[:500]:
        item = account.public(mask=True)
        sheet.append([item['username'], item['display_name'], item['phone'], item['status']])
    buffer = BytesIO()
    book.save(buffer)
    response = HttpResponse(buffer.getvalue(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="users.xlsx"'
    return response


@csrf_exempt
@login_required
@require_http_methods(['POST'])
def excel_import(request):
    upload = request.FILES.get('file')
    if upload is None:
        return err('请上传文件')
    book = load_workbook(upload, read_only=True)
    sheet = book.active
    rows = []
    for index, row in enumerate(sheet.iter_rows(values_only=True)):
        if index == 0:
            continue
        rows.append([cell for cell in row])
        if len(rows) >= 200:
            break
    return ok({'count': len(rows), 'rows': rows[:20]})
