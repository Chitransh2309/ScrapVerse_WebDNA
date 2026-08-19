from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.db.session import get_db
from app.db.models.agent_models import AgentRun, AgentEvent

router = APIRouter()

@router.get("/companies/{company_id}/agent/runs")
async def get_agent_runs(company_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(AgentRun)
        .where(AgentRun.company_id == company_id)
        .order_by(desc(AgentRun.started_at))
    )
    runs = result.scalars().all()
    
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

