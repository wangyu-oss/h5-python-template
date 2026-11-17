from django.db.models import Count
from django.db.models.functions import TruncDate
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from common.auth import permission_required
from common.response import body, client_ip, err, ok, paginate
from track.models import ClientError, IpBlacklist, TrackEvent


@csrf_exempt
@require_http_methods(['POST'])
def events(request):
    from common.scope import module_open
    if not module_open('module_track'):
        return ok({'accepted': 0})
    data = body(request) or {}
    items = data.get('events') or []
    if not isinstance(items, list):
        return err('参数错误')
    account = getattr(request, 'account', None)
    ip = client_ip(request)[:64]
    rows = []
    for item in items[:50]:
        if not isinstance(item, dict) or not item.get('name'):
            continue
        rows.append(TrackEvent(
            account=account,
            name=str(item.get('name'))[:64],
            page=str(item.get('page') or '')[:128],
            props=_clean_props(item.get('props') if isinstance(item.get('props'), dict) else {}),
            tenant_id=getattr(account, 'tenant_id', None),
            device=str(item.get('device') or data.get('device') or '')[:64],
            os_name=str(item.get('os') or data.get('os') or '')[:64],
            browser=str(item.get('browser') or data.get('browser') or '')[:64],
            network=str(item.get('network') or data.get('network') or '')[:32],
            ip=ip,
        ))
    TrackEvent.objects.bulk_create(rows)
    return ok({'accepted': len(rows)})


@csrf_exempt
@require_http_methods(['POST'])
def errors(request):
    data = body(request) or {}
    message = (data.get('message') or '').strip()
    if not message:
        return err('缺少错误信息')
    ClientError.objects.create(
        account=getattr(request, 'account', None),
        kind=(data.get('kind') or 'js')[:32],
        message=message[:500],
        page=(data.get('page') or '')[:255],
        detail=(data.get('detail') or '')[:4000],
    )
    return ok({'reported': True})


def _clean_props(props):
    blocked = ('phone', 'mobile', 'id_card', 'password', 'token')
    return {key: value for key, value in props.items() if key.lower() not in blocked}


@csrf_exempt
@permission_required('admin:track')
@require_http_methods(['GET', 'POST'])
def catalog(request):
    from common.scope import tenant_qs
    from track.models import TrackCatalog
    if request.method == 'GET':
        return ok({'items': [row.public() for row in tenant_qs(request, TrackCatalog.objects.all())]})
    data = body(request) or {}
    name = (data.get('name') or '').strip()
    if not name:
        return err('请填写事件名')
    from common.scope import current_tenant_id
    row, _ = TrackCatalog.objects.update_or_create(
        tenant_id=current_tenant_id(request),
        name=name[:64],
        defaults={'title': (data.get('title') or name)[:80], 'enabled': bool(data.get('enabled', True))},
    )
    return ok(row.public())


def summary(request):
    days = list(
        TrackEvent.objects.annotate(day=TruncDate('created_at')).values('day').annotate(total=Count('id')).order_by('-day')[:14]
    )
    for row in days:
        row['day'] = row['day'].isoformat() if row['day'] else ''
    names = list(TrackEvent.objects.values('name').annotate(total=Count('id')).order_by('-total')[:10])
    return ok({
        'total': TrackEvent.objects.count(),
        'errors': ClientError.objects.count(),
        'days': days,
        'names': names,
    })


@csrf_exempt
@permission_required('admin:track')
@require_http_methods(['GET'])
def event_list(request):
    total, rows = paginate(request, TrackEvent.objects.select_related('account'))
    return ok({'items': [row.public() for row in rows], 'total': total})


@csrf_exempt
@permission_required('admin:track')
@require_http_methods(['GET'])
def error_list(request):
    total, rows = paginate(request, ClientError.objects.all())
    return ok({'items': [row.public() for row in rows], 'total': total})


@csrf_exempt
@permission_required('admin:track')
@require_http_methods(['GET'])
def blacklist(request):
    return ok({'items': [row.public() for row in IpBlacklist.objects.all()]})


@csrf_exempt
@permission_required('admin:track')
@require_http_methods(['POST'])
def blacklist_save(request):
    data = body(request) or {}
    ip = (data.get('ip') or '').strip()
    if not ip:
        return err('请填写 IP')
    row, _ = IpBlacklist.objects.update_or_create(ip=ip[:64], defaults={
        'reason': (data.get('reason') or '')[:200],
        'enabled': bool(data.get('enabled', True)),
    })
    return ok(row.public())


@csrf_exempt
@permission_required('admin:track')
@require_http_methods(['POST'])
def blacklist_delete(request):
    data = body(request) or {}
    IpBlacklist.objects.filter(id=data.get('id')).delete()
    return ok({'deleted': True})
