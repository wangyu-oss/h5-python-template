import hashlib
import hmac
import time

from django.conf import settings
from django.core.cache import cache


def mask_phone(phone):
    phone = phone or ''
    if len(phone) < 7:
        return phone
    return f'{phone[:3]}****{phone[-4:]}'


def mask_id_card(value):
    value = value or ''
    if len(value) < 8:
        return value
    return f'{value[:4]}**********{value[-4:]}'


def hash_text(value):
    return hashlib.sha256(value.encode('utf-8')).hexdigest()


def sign_payload(secret, payload):
    return hmac.new(secret.encode('utf-8'), payload.encode('utf-8'), hashlib.sha256).hexdigest()


def verify_request_sign(request):
    secret = getattr(settings, 'SECRET_KEY', '')
    timestamp = request.headers.get('X-Timestamp', '')
    nonce = request.headers.get('X-Nonce', '')
    signature = request.headers.get('X-Sign', '')
    if not timestamp or not nonce or not signature:
        return False
    try:
        ts = int(timestamp)
    except ValueError:
        return False
    if abs(time.time() - ts) > 300:
        return False
    if not cache.add(f'sign-nonce:{nonce}', 1, 300):
        return False
    body = request.body.decode('utf-8') if request.body else ''
    payload = f'{request.method}\n{request.path}\n{timestamp}\n{nonce}\n{body}'
    expected = sign_payload(secret, payload)
    return hmac.compare_digest(expected, signature)


def cache_lock(name, ttl=10):
    key = f'lock:{name}'
    return cache.add(key, 1, ttl)


def cache_unlock(name):
    cache.delete(f'lock:{name}')
