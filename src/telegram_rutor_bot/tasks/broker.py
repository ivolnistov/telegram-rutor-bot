"""TaskIQ broker configuration"""

from taskiq import InMemoryBroker, TaskiqScheduler
from taskiq.schedule_sources import LabelScheduleSource

from telegram_rutor_bot.config import settings

# Create broker instance
# Use Redis if redis_url is configured, otherwise use InMemoryBroker
if settings.redis_url:
    from taskiq_redis import ListQueueBroker

    broker: InMemoryBroker | ListQueueBroker = ListQueueBroker(settings.redis_url)
else:
    broker = InMemoryBroker()

# Create scheduler
scheduler = TaskiqScheduler(
    broker=broker,
    sources=[LabelScheduleSource(broker)],
)


async def startup() -> None:
    """Startup tasks"""
    if not broker.is_worker_process:
        await broker.startup()
        # Start scheduler in the main process
        await scheduler.startup()


async def shutdown() -> None:
    """Shutdown tasks"""
    if not broker.is_worker_process:
        await scheduler.shutdown()
        await broker.shutdown()
