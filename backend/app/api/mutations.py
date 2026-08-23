from datetime import datetime, timedelta
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.db.session import get_db
from app.db.models.mutation_models import MutationCandidate
from app.db.models.agent_models import AgentRun

router = APIRouter()

INVESTIGATION_STALE_AFTER = timedelta(minutes=10)

@router.get("")
async def get_mutations(company_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(MutationCandidate)
        .where(MutationCandidate.company_id == company_id)
        .order_by(desc(MutationCandidate.created_at))
    )
    mutations = result.scalars().all()

    # A mutation can be left stuck at "investigating" forever if the server
    # restarted between marking it as such and actually creating/finishing
    # its AgentRun. Detect and clear that instead of leaving it misleading.
    now = datetime.utcnow()
    dirty = False
    for m in mutations:
        if m.investigation_status != "investigating":
            continue
        run_result = await db.execute(
            select(AgentRun)
            .where(AgentRun.mutation_id == m.id)
            .order_by(desc(AgentRun.started_at))
            .limit(1)
        )
        run = run_result.scalar_one_or_none()
        if run is None or (run.status == "running" and now - run.started_at > INVESTIGATION_STALE_AFTER):
            m.investigation_status = "failed"
            if run is not None:
                run.status = "failed"
            dirty = True
    if dirty:
        await db.commit()

    return [
        {
            "id": m.id,
            "trait": m.trait,
            "old_value": m.old_value,
            "new_value": m.new_value,
            "delta": m.delta,
            "percentage_change": m.percentage_change,
            "mutation_type": m.mutation_type,
            "severity": m.severity,
            "confidence": m.confidence,
            "investigation_status": m.investigation_status,
            "created_at": m.created_at
        } for m in mutations
    ]

@router.get("/{mutation_id}")
async def get_mutation(company_id: str, mutation_id: str, db: AsyncSession = Depends(get_db)):
    m = await db.get(MutationCandidate, mutation_id)
    if not m:
        return {"error": "Not found"}
        
    return {
        "id": m.id,
        "trait": m.trait,
        "old_value": m.old_value,
        "new_value": m.new_value,
        "delta": m.delta,
        "percentage_change": m.percentage_change,
        "mutation_type": m.mutation_type,
        "severity": m.severity,
        "confidence": m.confidence,
        "evidence_ids": m.evidence_ids,
        "investigation_status": m.investigation_status,
        "final_explanation": m.final_explanation,
        "created_at": m.created_at
    }

