"""ARKON Worker - Background job processing.

Consumes jobs from the queue and executes them.
Runs as a separate process from the API server.
"""

import asyncio
import signal
from collections.abc import AsyncGenerator

import structlog
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.logging import setup_logging
from app.database.engine import create_engine, dispose_engine, get_session_factory
from app.models.domain import Job

logger = structlog.get_logger(__name__)

_running = True


def handle_signal(signum: int, frame: object) -> None:
    """Handle shutdown signals."""
    global _running
    logger.info("worker_shutdown_requested", signal=signum)
    _running = False


async def poll_jobs() -> AsyncGenerator[Job, None]:
    """Poll for queued jobs."""
    factory = get_session_factory()
    async with factory() as session:
        result = await session.execute(
            select(Job)
            .where(Job.status == "queued")
            .order_by(Job.priority.desc(), Job.created_at.asc())
            .limit(10)
        )
        jobs = result.scalars().all()
        for job in jobs:
            yield job


async def process_job(job: Job) -> None:
    """Process a single job."""
    logger.info("job_processing", job_id=str(job.id), name=job.name)
    factory = get_session_factory()
    async with factory() as session:
        job_record = await session.get(Job, job.id)
        if job_record is None:
            return

        job_record.status = "running"
        job_record.started_at = func.now()
        await session.commit()

        try:
            # TODO: Route to appropriate executor based on job type
            job_record.status = "completed"
            job_record.completed_at = func.now()
            job_record.output_data = {"result": "processed"}
            await session.commit()
            logger.info("job_completed", job_id=str(job.id))
        except Exception as e:
            job_record.status = "failed"
            job_record.error_message = str(e)
            await session.commit()
            logger.error("job_failed", job_id=str(job.id), error=str(e))


async def run_worker() -> None:
    """Main worker loop."""
    global _running

    setup_logging(log_level=settings.LOG_LEVEL, log_format=settings.LOG_FORMAT)
    logger.info("worker_started", worker_id="worker-1")

    await create_engine()

    while _running:
        try:
            async for job in poll_jobs():
                if not _running:
                    break
                await process_job(job)
        except Exception as e:
            logger.error("worker_error", error=str(e))

        await asyncio.sleep(1)

    await dispose_engine()
    logger.info("worker_stopped")


def main() -> None:
    """Entry point for the worker."""
    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)
    asyncio.run(run_worker())


if __name__ == "__main__":
    main()
