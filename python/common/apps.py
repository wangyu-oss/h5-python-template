from django.apps import AppConfig


class CommonConfig(AppConfig):
    name = 'common'
    verbose_name = '公共'

    def ready(self):
        from common import signals  # noqa: F401
