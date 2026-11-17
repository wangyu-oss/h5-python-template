from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from common.response import err, ok
from common.settings_store import setting

ENDPOINTS = [
    ['GET', '/api/v1/health', '健康检查'],
    ['POST', '/api/v1/auth/login', '账号密码登录'],
    ['POST', '/api/v1/auth/sms/send', '发送验证码'],
    ['POST', '/api/v1/auth/sms/login', '验证码登录'],
    ['POST', '/api/v1/auth/guest', '游客登录'],
    ['POST', '/api/v1/auth/refresh', '刷新访问令牌'],
    ['POST', '/api/v1/auth/logout', '退出'],
    ['GET', '/api/v1/auth/me', '当前用户'],
    ['GET', '/api/v1/config/public', 'H5 公共配置'],
    ['POST', '/api/v1/files/upload', '上传文件'],
    ['POST', '/api/v1/pay/orders', '创建订单'],
    ['POST', '/api/v1/track/events', '批量埋点'],
    ['POST', '/api/v1/plugins/checkin', '签到'],
]


def _allowed(request):
    password = setting('doc_password', '')
    if not password:
        return True
    header = request.headers.get('Authorization', '')
    return header == f'Bearer {password}' or request.GET.get('password') == password


@csrf_exempt
@require_http_methods(['GET'])
def schema(request):
    if not _allowed(request):
        return err('文档需要密码', 401, 401)
    return ok({'openapi': '3.0.0', 'info': {'title': 'H5 Template API', 'version': '1.0.0'}, 'paths': {
        path: {method.lower(): {'summary': summary}} for method, path, summary in ENDPOINTS
    }})


@csrf_exempt
@require_http_methods(['GET'])
def docs(request):
    if not _allowed(request):
        return HttpResponse('文档需要密码', status=401)
    rows = ''.join(f'<tr><td>{method}</td><td>{path}</td><td>{summary}</td></tr>' for method, path, summary in ENDPOINTS)
    html = f'''<!doctype html><html><head><meta charset="utf-8"><title>API Docs</title>
<style>body{{font-family:sans-serif;margin:24px}}table{{border-collapse:collapse;width:100%}}td,th{{border:1px solid #ddd;padding:8px;text-align:left}}</style>
</head><body><h1>H5 Template API</h1><p>统一响应 code / msg / data，code 为 0 表示成功。</p>
<table><thead><tr><th>方法</th><th>路径</th><th>说明</th></tr></thead><tbody>{rows}</tbody></table>
<p>机器可读描述：<a href="/api/schema">/api/schema</a></p></body></html>'''
    return HttpResponse(html)
