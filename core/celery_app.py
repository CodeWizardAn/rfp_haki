"""
Enterprise Celery Application Configuration
Provides asynchronous task queues for heavy RFP extraction, spec comparison,
and multi-agent execution.
"""

import os
from celery import Celery

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery(
    "haki_fmcg_worker",
    broker=os.getenv("CELERY_BROKER_URL", REDIS_URL),
    backend=os.getenv("CELERY_RESULT_BACKEND", REDIS_URL),
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,  # 5 minutes maximum for any RFP pipeline task
    task_soft_time_limit=240,  # 4 minutes soft limit for graceful cleanup
    worker_concurrency=int(os.getenv("CELERY_WORKER_CONCURRENCY", "4")),
    worker_prefetch_multiplier=1,  # Prevent worker greediness on long-running AI tasks
    task_acks_late=True,  # Re-queue task if worker crashes during execution
    task_reject_on_worker_lost=True,
)

# Example task definition for asynchronous RFP processing
@celery_app.task(bind=True, name="tasks.process_rfp_pipeline")
def process_rfp_pipeline_task(self, rfp_id: int, file_path: str, tenant_id: str = "default"):
    """
    Celery task that executes full RFP pipeline in a dedicated worker process.
    """
    import logging
    logger = logging.getLogger("celery.task")
    logger.info(f"Starting Celery task for RFP {rfp_id} (tenant: {tenant_id})")

    try:
        from pipeline_connector import PipelineExecutor
        executor = PipelineExecutor()
        # Update task progress state
        self.update_state(state="PROCESSING", meta={"progress": 25, "step": "Document Extraction"})
        
        result = executor.process_rfp(rfp_id=rfp_id, file_path=file_path)
        
        self.update_state(state="SUCCESS", meta={"progress": 100, "result": result})
        return result
    except Exception as exc:
        logger.error(f"Failed RFP processing in Celery: {exc}")
        self.update_state(state="FAILURE", meta={"error": str(exc)})
        raise exc
