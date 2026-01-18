"""Task execution broker configuration."""

import logging
from datetime import UTC, datetime, timedelta

from sqlalchemy import update
from taskiq import InMemoryBroker, TaskiqEvents, TaskiqScheduler, TaskiqState
from taskiq.schedule_sources import LabelScheduleSource

from telegram_rutor_bot.config import settings
from telegram_rutor_bot.db import get_async_session, init_db
from telegram_rutor_bot.db.models import TaskExecution

log = logging.getLogger(__name__)

# Create broker instance
# Use Redis if redis_url is configured, otherwise use InMemoryBroker
if settings.redis_url:
    from taskiq_redis import ListQueueBroker

    log.debug('Using Redis Broker at %s', settings.redis_url)
    broker: InMemoryBroker | ListQueueBroker = ListQueueBroker(settings.redis_url, queue_name='rutor_tasks')
else:
    log.debug('Using InMemoryBroker')
    broker = InMemoryBroker()

# Create scheduler
scheduler = TaskiqScheduler(
    broker=broker,
    sources=[LabelScheduleSource(broker)],
)


@broker.on_event(TaskiqEvents.WORKER_STARTUP)
async def startup(_: TaskiqState) -> None:
    """Startup tasks"""
    log.debug('Worker Startup Event Called!')
    init_db()

    # Clean up stale pending tasks (older than 5 minutes)
    # This is safe for multi-worker setups as we only cancel tasks that are clearly stuck/abandoned
    try:
        async with get_async_session() as session:
            stmt = (
                update(TaskExecution)
                .where(
                    TaskExecution.status == 'pending',
                    TaskExecution.start_time < datetime.now(UTC) - timedelta(minutes=5),
                )
                .values(
                    status='cancelled',
                    result='Cancelled on worker startup (stale)',
                    end_time=datetime.now(UTC),
                )
            )
            await session.execute(stmt)
            await session.commit()
            log.debug('Cleaned up stale pending tasks')
    except Exception as e:  # pylint: disable=broad-exception-caught
        log.error('Failed to cleanup stale tasks: %s', e)


@broker.on_event(TaskiqEvents.WORKER_SHUTDOWN)
async def shutdown(_: TaskiqState) -> None:
    """Shutdown tasks"""


# Import jobs to register tasks
