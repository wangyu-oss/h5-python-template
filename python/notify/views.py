from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from common.audit import log_op
from common.auth import login_required, permission_required
from common.response import body, err, ok, paginate
from notify.models import InboxMessage, MessageTemplate
from notify.providers import ProviderError, render, send_mail, send_sms


@csrf_exempt
@login_required
@require_http_methods(['GET'])
def messages(request):
    from django.db.models import Q
    from django.utils import timezone
    now = timezone.now()
    qs = InboxMessage.objects.filter(account=request.account).filter(Q(expire_at__isnull=True) | Q(expire_at__gt=now))
    category = (request.GET.get('category') or '').strip()
    if category:
        qs = qs.filter(category=category)
    total, rows = paginate(request, qs)
    return ok({'items': [row.public() for row in rows], 'total': total})


@csrf_exempt
@login_required
@require_http_methods(['GET'])
def unread(request):
    count = InboxMessage.objects.filter(account=request.account, is_read=False).count()
    return ok({'count': count})


@csrf_exempt
@login_required
@require_http_methods(['POST'])
def message_read(request):
    data = body(request) or {}
    qs = InboxMessage.objects.filter(account=request.account, is_read=False)
    if data.get('id'):
        qs = qs.filter(id=data['id'])
    updated = qs.update(is_read=True)
    return ok({'updated': updated})


@csrf_exempt
@permission_required('admin:sms')
@require_http_methods(['GET'])
def templates(request):
    return ok({'items': [row.public() for row in MessageTemplate.objects.all()]})


@csrf_exempt
@permission_required('admin:sms')
@require_http_methods(['POST'])
def template_save(request):
    data = body(request) or {}
    if data.get('id'):
        row = MessageTemplate.objects.filter(id=data['id']).first()
        if row is None:
            return err('模板不存在')
    else:
        code = (data.get('code') or '').strip()
        if not code:
            return err('请填写模板编码')
        row = MessageTemplate(code=code)
    row.channel = (data.get('channel') or row.channel or 'inbox')[:16]
    row.title = (data.get('title') or '')[:120]
    row.content = data.get('content') or ''
    row.enabled = bool(data.get('enabled', True))
    if data.get('code'):
        row.code = data['code'][:64]
    row.save()
    log_op(request, 'template_save', row.code)
    return ok(row.public())


@csrf_exempt
@permission_required('admin:sms')
@require_http_methods(['POST'])
def sms_test(request):
    data = body(request) or {}
    phone = (data.get('phone') or '').strip()
    content = data.get('content') or '测试短信'
    template = MessageTemplate.objects.filter(code=data.get('code') or '', enabled=True).first()
    if template:
        content = render(template.content, data.get('params') or {})
    from notify.models import MessageSendLog
    try:
        result = send_sms(phone, content)
        MessageSendLog.objects.create(channel='sms', target=phone, content=content[:500], success=True)
    except ProviderError as exc:
        MessageSendLog.objects.create(channel='sms', target=phone, content=content[:500], success=False, error=str(exc)[:200])
        return err(str(exc))
    return ok(result)


@csrf_exempt
@permission_required('admin:sms')
@require_http_methods(['POST'])
def mail_test(request):
    data = body(request) or {}
    try:
        result = send_mail(data.get('email') or '', data.get('title') or '测试邮件', data.get('content') or 'hello')
    except Exception as exc:
        return err(str(exc))
    return ok(result)


@csrf_exempt
@permission_required('admin:sms')
@require_http_methods(['POST'])
def inbox_send(request):
    data = body(request) or {}
    from accounts.models import Account
    account = Account.objects.filter(id=data.get('account_id'), is_deleted=False).first()
    if account is None:
        return err('用户不存在')
    message = InboxMessage.objects.create(account=account, title=(data.get('title') or '通知')[:120], content=data.get('content') or '')
    return ok(message.public())
