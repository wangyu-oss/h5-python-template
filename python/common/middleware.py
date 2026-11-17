import logging
import time
import uuid

from django.conf import settings
from django.core.cache import cache

from common.context import set_current_account
from common.response import client_ip, err

logger = logging.getLogger('api')


class ExceptionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            return self.get_response(request)
        except Exception:
            logger.exception('unhandled path=%s', request.path)
            if request.path.startswith('/api/'):
                return err('服务器错误', 500, 500)
            raise


class TraceMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.trace_id = (request.headers.get('X-Trace-Id') or uuid.uuid4().hex)[:64]
        request._started = time.perf_counter()
        response = self.get_response(request)
        response['X-Trace-Id'] = request.trace_id
        return response


class ApiLogMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        path = request.path
        if not path.startswith('/api/') or path.endswith('/health'):
            return response
        try:
            from system.models import ApiLog
            ApiLog.objects.create(
                trace_id=getattr(request, 'trace_id', ''),
                method=request.method,
                path=path[:255],
                status_code=getattr(response, 'status_code', 0),
                duration_ms=int((time.perf_counter() - getattr(request, '_started', time.perf_counter())) * 1000),
                ip=client_ip(request)[:64],
                account=getattr(request, 'account', None),
            )
        except Exception:
            logger.debug('skip api log', exc_info=True)
        return response


class BlacklistMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith('/api/'):
            try:
                from track.models import IpBlacklist
                ip = client_ip(request)
                if ip and IpBlacklist.objects.filter(ip=ip, enabled=True).exists():
                    return err('访问被拒绝', 403, 403)
            except Exception:
                pass
        return self.get_response(request)


class RateLimitMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if settings.TESTING or not request.path.startswith('/api/') or request.path.endswith('/health'):
            return self.get_response(request)
        ip = client_ip(request) or 'unknown'
        limit = 300
        try:
            from common.settings_store import setting_int
            limit = setting_int('rate_limit_ip', 300)
        except Exception:
            pass
        key = f'rate:{ip}:{int(time.time() // 60)}'
        count = cache.get(key, 0) + 1
        cache.set(key, count, 70)
        if count > limit:
            return err('请求过于频繁', 429, 429)
        return self.get_response(request)


class SignMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not request.path.startswith('/api/') or request.path.endswith('/health'):
            return self.get_response(request)
        try:
            from common.settings_store import setting
            enabled = setting('api_sign', 'no') == 'yes'
        except Exception:
            enabled = False
        if not enabled:
            return self.get_response(request)
        from common.security import verify_request_sign
        if not verify_request_sign(request):
            return err('签名校验失败', 401, 401)
        return self.get_response(request)


class AuthMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.account = None
        request.session_row = None
        header = request.headers.get('Authorization', '')
        token = header[7:].strip() if header.startswith('Bearer ') else ''
        if token:
            from common.auth import touch_session
            session = touch_session(token)
            if session is not None:
                request.session_row = session
                request.account = session.account
        set_current_account(request.account)
        try:
            return self.get_response(request)
        finally:
            set_current_account(None)
