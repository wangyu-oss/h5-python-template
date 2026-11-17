import json

from django.http import JsonResponse


def ok(data=None, msg='ok'):
    return JsonResponse({'code': 0, 'msg': msg, 'data': data}, json_dumps_params={'ensure_ascii': False})


def err(msg, code=400, status=None, data=None):
    return JsonResponse(
        {'code': code, 'msg': msg, 'data': data},
        status=status or code,
        json_dumps_params={'ensure_ascii': False},
    )


def body(request):
    if not request.body:
        return {}
    try:
        data = json.loads(request.body.decode('utf-8'))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None
    return data if isinstance(data, dict) else None


def client_ip(request):
    forwarded = request.META.get('HTTP_X_FORWARDED_FOR', '')
    if forwarded:
        return forwarded.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '') or ''


def paginate(request, qs):
    try:
        page = max(int(request.GET.get('page') or 1), 1)
        size = min(max(int(request.GET.get('page_size') or 10), 1), 200)
    except ValueError:
        page, size = 1, 10
    total = qs.count()
    start = (page - 1) * size
    return total, list(qs[start:start + size])
