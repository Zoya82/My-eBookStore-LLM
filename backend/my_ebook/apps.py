from django.apps import AppConfig
import os


class MyEbookConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'my_ebook'

    def ready(self):
        # 只在子进程（RUN_MAIN=true）中启动调度器
        if os.environ.get('RUN_MAIN') == 'true':
            from my_ebook.scheduler import start_scheduler
            start_scheduler()