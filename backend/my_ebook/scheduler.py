from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.memory import MemoryJobStore  #改用内存存储
from django.utils import timezone
from datetime import timedelta
from apps.orders.models import Order
import logging
import os

logger = logging.getLogger(__name__)


def auto_confirm_receive_job():
    """自动确认收货任务：将发货超过7天且未确认的订单自动变为已完成"""
    seven_days_ago = timezone.now() - timedelta(days=7)

    count = Order.objects.filter(
        status=Order.STATUS_SHIPPED,
        ship_time__lte=seven_days_ago
    ).update(
        status=Order.STATUS_COMPLETED,
        receive_time=timezone.now()
    )

    if count > 0:
        print(f'✅ 自动确认收货了 {count} 笔订单。')
        logger.info(f'✅ 自动确认收货了 {count} 笔订单。')


def start_scheduler():
    # 防止重复启动
    if hasattr(start_scheduler, '_started') and start_scheduler._started:
        return

    # 只在实际处理请求的子进程中启动
    if os.environ.get('RUN_MAIN') != 'true':
        print("⚠️ 调度器在父进程中跳过启动（等待子进程启动）")
        return

    try:
        # 使用内存存储（不会访问数据库，避免 SQLite 锁）
        scheduler = BackgroundScheduler()
        scheduler.add_jobstore(MemoryJobStore(), 'default')  #改用内存存储

        # 每天凌晨 2:00 执行一次
        scheduler.add_job(
            auto_confirm_receive_job,
            trigger='cron',
            hour=2,
            minute=0,
            #second=5,      #调试用
            id='auto_confirm_receive',
            replace_existing=True,
        )

        scheduler.start()
        print('🚀 【调度器】自动确认收货调度器已安全启动（内存模式），每天凌晨2:00执行。')
        logger.info('🚀 【调度器】自动确认收货调度器已安全启动（内存模式），每天凌晨2:00执行。')

        # 标记为已启动
        start_scheduler._started = True

    except Exception as e:
        print(f'⚠️ 调度器启动失败（不影响业务）：{e}')