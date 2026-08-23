from datetime import datetime, timedelta
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.db.session import get_db
from app.db.models.agent_models import AgentRun, AgentEvent
from app.db.models.mutation_models import MutationCandidate

router = APIRouter()

AGENT_RUN_STALE_AFTER = timedelta(minutes=10)

@router.get("/companies/{company_id}/agent/runs")
async def get_agent_runs(company_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(AgentRun)
        .where(AgentRun.company_id == company_id)
        .order_by(desc(AgentRun.started_at))
    )
    runs = result.scalars().all()

    # A run stuck "running" for too long was almost certainly abandoned by a
    # server restart mid-investigation and will never update on its own.
    now = datetime.utcnow()
    dirty = False
    for r in runs:
        if r.status == "running" and now - r.started_at > AGENT_RUN_STALE_AFTER:
            r.status = "failed"
            mutation = await db.get(MutationCandidate, r.mutation_id)
            if mutation and mutation.investigation_status == "investigating":
                mutation.investigation_status = "failed"
            dirty = True
    if dirty:
        await db.commit()

    return [
        {
            "id": r.id,
            "mutation_id": r.mutation_id,
            "status": r.status,
            "step_count": r.step_count,
            "final_result": r.final_result,
            "started_at": r.started_at,
            "completed_at": r.completed_at
        } for r in runs
    ]

@router.get("/agent/runs/{run_id}/events")
async def get_agent_events(run_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(AgentEvent)
        .where(AgentEvent.agent_run_id == run_id)
        .order_by(AgentEvent.timestamp)
    )
    events = result.scalars().all()
    
    return [
        {
            "id": e.id,
            "event_type": e.event_type,
            "status": e.status,
            "input_summary": e.input_summary,
            "output_summary": e.output_summary,
            "timestamp": e.timestamp
        } for e in events
    ]

