from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.db.models.core import SequenceJob
from app.services.sequencing import run_sequence_job
import uuid

router = APIRouter()

TERMINAL_STATUSES = {"completed", "failed"}
STALE_AFTER = timedelta(minutes=5)

@router.post("")
async def create_sequence(company_id: str, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    job = SequenceJob(company_id=company_id, status="queued")
    db.add(job)
    await db.commit()

    background_tasks.add_task(run_sequence_job, job.id, company_id, db)

    return {"job_id": job.id, "status": "queued"}

@router.get("/{job_id}")
async def get_sequence(company_id: str, job_id: str, db: AsyncSession = Depends(get_db)):
    job = await db.get(SequenceJob, job_id)
    if not job:
        return {"error": "Job not found"}

    # A job that hasn't progressed in a while was likely abandoned mid-flight
    # (e.g. a server restart/redeploy killed its background task) and will
    # never reach a terminal status on its own - surface that instead of
    # leaving callers polling forever.
    if job.status not in TERMINAL_STATUSES and datetime.utcnow() - job.updated_at > STALE_AFTER:
        job.status = "failed"
        await db.commit()

    return {"job_id": job.id, "status": job.status}

