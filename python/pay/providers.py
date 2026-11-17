import os

from common.settings_store import setting


class ProviderError(Exception):
    pass


def resolve_channel(requested):
    channel = requested or setting('pay_channel', 'mock') or 'mock'
    return channel


def create_payment(order):
    if order.channel == 'mock':
        return {
            'channel': 'mock',
            'order_no': order.order_no,
            'mock_notify': f'/api/v1/pay/orders/{order.order_no}/mock-notify',
        }
    if order.channel == 'wechat':
        if not os.getenv('WECHAT_MCH_ID') or not os.getenv('WECHAT_API_V3_KEY'):
            raise ProviderError('未配置微信支付')
        return {
            'channel': 'wechat',
            'appId': os.getenv('WECHAT_APP_ID', ''),
            'order_no': order.order_no,
            'package': f'prepay_id={order.order_no}',
        }
    if order.channel == 'alipay':
        if not os.getenv('ALIPAY_APP_ID') or not os.getenv('ALIPAY_PRIVATE_KEY'):
            raise ProviderError('未配置支付宝')
        return {'channel': 'alipay', 'order_no': order.order_no, 'pay_url': f'/pay/alipay/{order.order_no}'}
    raise ProviderError('未知支付渠道')
