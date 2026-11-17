import secrets
from datetime import timedelta

from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from common.audit import log_op
from common.auth import idempotent, permission_required
from common.response import body, err, ok, paginate
from common.security import cache_lock, cache_unlock
from pay.models import PayOrder
from pay.providers import ProviderError, create_payment, resolve_channel


@csrf_exempt
@permission_required('h5:pay')
@idempotent
@require_http_methods(['POST'])
def order_create(request):
    from common.scope import require_module
    closed = require_module('module_order')
    if closed:
        return closed
    data = body(request) or {}
    subject = (data.get('subject') or '演示订单').strip()[:120]
    try:
        amount = int(data.get('amount') or 1)
    except (TypeError, ValueError):
        return err('金额不正确')
    if amount <= 0:
        return err('金额不正确')
    idem = request.headers.get('Idempotency-Key', '')[:64]
    if idem:
        existed = PayOrder.objects.filter(account=request.account, idempotency_key=idem).first()
        if existed:
            return ok({'order': existed.public(), 'pay': {'reused': True}})
    if not cache_lock(f'pay:{request.account.id}', 5):
        return err('请勿重复提交', 409, 409)
    try:
        channel = resolve_channel(data.get('channel'))
        order = PayOrder.objects.create(
            order_no=timezone.now().strftime('%Y%m%d%H%M%S') + secrets.token_hex(3),
            tenant_id=request.account.tenant_id,
            account=request.account,
            subject=subject,
            amount=amount,
            channel=channel,
            idempotency_key=idem,
            expire_at=timezone.now() + timedelta(minutes=30),
        )
        try:
            pay = create_payment(order)
        except ProviderError as exc:
            order.status = 'closed'
            order.save(update_fields=['status'])
            return err(str(exc))
    finally:
        cache_unlock(f'pay:{request.account.id}')
    log_op(request, 'pay_create', order.order_no)
    return ok({'order': order.public(), 'pay': pay})


@csrf_exempt
@permission_required('h5:pay')
@require_http_methods(['GET'])
def order_list(request):
    total, rows = paginate(request, PayOrder.objects.filter(account=request.account))
    return ok({'items': [row.public() for row in rows], 'total': total})


@csrf_exempt
@permission_required('h5:pay')
@require_http_methods(['GET'])
def order_detail(request, order_no):
    order = PayOrder.objects.filter(order_no=order_no, account=request.account).first()
    if order is None:
        return err('订单不存在', 404, 404)
    return ok(order.public())


@csrf_exempt
@permission_required('h5:pay')
@require_http_methods(['POST'])
def mock_notify(request, order_no):
    order = PayOrder.objects.filter(order_no=order_no).first()
    if order is None:
        return err('订单不存在', 404, 404)
    if order.channel != 'mock':
        return err('该订单不是模拟支付')
    if order.status == 'pending':
        order.status = 'paid'
        order.paid_at = timezone.now()
        order.save(update_fields=['status', 'paid_at', 'updated_at'])
        from pay.models import PayCallbackLog
        PayCallbackLog.objects.create(order=order, channel='mock', payload='mock-notify', success=True)
        from notify.models import InboxMessage
        InboxMessage.objects.create(account=order.account, title='支付成功', content=f'{order.subject} 已支付 {order.amount} 分')
    return ok(order.public(), '支付成功')


@csrf_exempt
@require_http_methods(['POST'])
def wechat_callback(request):
    return ok({'received': True, 'channel': 'wechat'})


@csrf_exempt
@require_http_methods(['POST'])
def alipay_callback(request):
    return ok({'received': True, 'channel': 'alipay'})


@csrf_exempt
@permission_required('admin:pay')
@require_http_methods(['GET'])
def admin_orders(request):
    from common.scope import tenant_qs
    qs = tenant_qs(request, PayOrder.objects.select_related('account'))
    status = (request.GET.get('status') or '').strip()
    channel = (request.GET.get('channel') or '').strip()
    keyword = (request.GET.get('keyword') or '').strip()
    if status:
        qs = qs.filter(status=status)
    if channel:
        qs = qs.filter(channel=channel)
    if keyword:
        qs = qs.filter(order_no__icontains=keyword) | qs.filter(subject__icontains=keyword)
    if request.GET.get('start'):
        qs = qs.filter(created_at__date__gte=request.GET.get('start'))
    if request.GET.get('end'):
        qs = qs.filter(created_at__date__lte=request.GET.get('end'))
    total, rows = paginate(request, qs.distinct())
    return ok({'items': [{**row.public(), 'username': row.account.username} for row in rows], 'total': total})


@csrf_exempt
@permission_required('admin:pay')
@require_http_methods(['GET'])
def admin_order_detail(request, order_no):
    from common.scope import tenant_qs
    order = tenant_qs(request, PayOrder.objects.select_related('account')).filter(order_no=order_no).first()
    if order is None:
        return err('订单不存在', 404, 404)
    data = order.public()
    data['username'] = order.account.username
    data['callbacks'] = [row.public() for row in order.callbacks.all().order_by('id')]
    return ok(data)


@csrf_exempt
@permission_required('admin:pay')
@require_http_methods(['POST'])
def order_remark(request, order_no):
    from common.scope import tenant_qs
    order = tenant_qs(request, PayOrder.objects.all()).filter(order_no=order_no).first()
    if order is None:
        return err('订单不存在', 404, 404)
    order.remark = ((body(request) or {}).get('remark') or '')[:200]
    order.save(update_fields=['remark', 'updated_at'])
    return ok(order.public())


@csrf_exempt
@permission_required('admin:pay')
@require_http_methods(['POST'])
def order_refund(request, order_no):
    from common.scope import tenant_qs
    from pay.models import PayCallbackLog
    order = tenant_qs(request, PayOrder.objects.all()).filter(order_no=order_no).first()
    if order is None:
        return err('订单不存在', 404, 404)
    if order.status != 'paid':
        return err('只有已支付订单可以退款')
    if order.channel != 'mock':
        return err('未配置真实退款渠道')
    order.status = 'refunded'
    order.save(update_fields=['status', 'updated_at'])
    PayCallbackLog.objects.create(order=order, channel=order.channel, payload='refund', success=True)
    log_op(request, 'pay_refund', order.order_no)
    return ok(order.public(), '已退款')
