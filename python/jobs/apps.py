from django.apps import AppConfig


class JobsConfig(AppConfig):
    name = 'jobs'
    verbose_name = '任务'

    def ready(self):
        from jobs.scheduler import start
        start()
