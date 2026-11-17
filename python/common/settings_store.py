from django.core.cache import cache


PUBLIC_KEYS = {
    'h5_title',
    'h5_primary',
    'h5_slogan',
    'h5_theme',
    'h5_watermark',
    'h5_locale',
    'feature_share',
    'feature_pay',
    'feature_dark',
    'feature_pwa',
    'privacy_version',
    'app_version',
    'register_enabled',
    'sms_provider',
    'pay_channel',
    'storage_provider',
    'plugin_checkin',
    'plugin_survey',
    'plugin_lottery',
    'plugin_vote',
    'plugin_points',
    'plugin_member',
    'plugin_comment',
    'plugin_map',
    'plugin_live',
    'plugin_ai',
    'plugin_contract',
    'plugin_ocr',
    'plugin_saas',
}


def setting(key, default='', tenant_id=None):
    cache_key = f'setting:{tenant_id or 0}:{key}'
    hit = cache.get(cache_key)
    if hit is not None:
        return hit
    from system.models import Setting
    row = None
    if tenant_id:
        row = Setting.objects.filter(key=key, tenant_id=tenant_id).first()
    if row is None:
        row = Setting.objects.filter(key=key, tenant__isnull=True).first()
    value = row.value if row else default
    cache.set(cache_key, value, 30)
    return value


def setting_int(key, default):
    try:
        return int(setting(key, default))
    except (TypeError, ValueError):
        return default


def clear_setting_cache(key=None):
    if key:
        cache.delete(f'setting:0:{key}')
        cache.delete(f'setting:{key}')
        return
    cache.clear()
