from common.response import client_ip


def log_login(username, success, message, request, tenant_id=None):
    from system.models import LoginLog
    LoginLog.objects.create(
        tenant_id=tenant_id,
        username=(username or '')[:64],
        success=success,
        message=(message or '')[:200],
        ip=client_ip(request)[:64],
        user_agent=(request.META.get('HTTP_USER_AGENT') or '')[:255],
    )


def log_op(request, action, target='', detail=''):
    from system.models import OperationLog
    account = getattr(request, 'account', None)
    OperationLog.objects.create(
        tenant_id=getattr(account, 'tenant_id', None),
        account=account,
        action=action[:64],
        target=str(target)[:120],
        detail=str(detail)[:2000],
        ip=client_ip(request)[:64],
    )
