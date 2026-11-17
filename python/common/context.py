import threading

_ctx = threading.local()


def set_current_account(account):
    _ctx.account = account


def get_current_account():
    return getattr(_ctx, 'account', None)
