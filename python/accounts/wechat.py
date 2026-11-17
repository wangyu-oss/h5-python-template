import os

import requests


class ProviderError(Exception):
    pass


def _mock(code, nickname):
    return {'openid': code or 'mock-openid', 'nickname': nickname, 'mock': True}


def official_login(code):
    app_id = os.getenv('WECHAT_APP_ID', '').strip()
    secret = os.getenv('WECHAT_APP_SECRET', '').strip()
    if not app_id or not secret:
        return _mock(code, '微信用户')
    response = requests.get(
        'https://api.weixin.qq.com/sns/oauth2/access_token',
        params={'appid': app_id, 'secret': secret, 'code': code, 'grant_type': 'authorization_code'},
        timeout=8,
    )
    data = response.json()
    if not data.get('openid'):
        raise ProviderError(data.get('errmsg') or '微信授权失败')
    return {'openid': data['openid'], 'unionid': data.get('unionid', ''), 'nickname': '微信用户', 'mock': False}


def mini_login(code):
    app_id = os.getenv('WECHAT_MINI_APP_ID', '').strip()
    secret = os.getenv('WECHAT_MINI_SECRET', '').strip()
    if not app_id or not secret:
        return _mock(code or 'mini-mock', '小程序用户')
    response = requests.get(
        'https://api.weixin.qq.com/sns/jscode2session',
        params={'appid': app_id, 'secret': secret, 'js_code': code, 'grant_type': 'authorization_code'},
        timeout=8,
    )
    data = response.json()
    if not data.get('openid'):
        raise ProviderError(data.get('errmsg') or '小程序授权失败')
    return {'openid': data['openid'], 'unionid': data.get('unionid', ''), 'nickname': '小程序用户', 'mock': False}


def jsconfig(url):
    import hashlib
    import time
    import uuid
    app_id = os.getenv('WECHAT_APP_ID', '').strip()
    secret = os.getenv('WECHAT_APP_SECRET', '').strip()
    timestamp = int(time.time())
    nonce = uuid.uuid4().hex
    if not app_id or not secret:
        return {
            'configured': False,
            'appId': '',
            'timestamp': timestamp,
            'nonceStr': nonce,
            'signature': '',
        }
    token_resp = requests.get(
        'https://api.weixin.qq.com/cgi-bin/token',
        params={'grant_type': 'client_credential', 'appid': app_id, 'secret': secret},
        timeout=8,
    ).json()
    ticket_resp = requests.get(
        'https://api.weixin.qq.com/cgi-bin/ticket/getticket',
        params={'access_token': token_resp.get('access_token', ''), 'type': 'jsapi'},
        timeout=8,
    ).json()
    ticket = ticket_resp.get('ticket', '')
    raw = f'jsapi_ticket={ticket}&noncestr={nonce}&timestamp={timestamp}&url={url}'
    signature = hashlib.sha1(raw.encode('utf-8')).hexdigest()
    return {'configured': True, 'appId': app_id, 'timestamp': timestamp, 'nonceStr': nonce, 'signature': signature}
