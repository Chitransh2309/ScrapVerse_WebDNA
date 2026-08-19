from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.db.models.core import SequenceJob
from app.services.sequencing import run_sequence_job
import uuid

router = APIRouter()

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
    return {"job_id": job.id, "status": job.status}

