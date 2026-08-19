from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import get_db
from app.db.models.evidence_models import Evidence

router = APIRouter()

@router.get("")
async def get_evidence(company_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Evidence).where(Evidence.company_id == company_id))
    evidence_records = result.scalars().all()
    
    return [
        {
            "id": ev.id,
            "trait": ev.trait,
            "type": ev.type,
            "title": ev.title,
            "content": ev.content,
            "url": ev.url,
            "source": ev.source,
            "confidence": ev.confidence,
            "observed_at": ev.observed_at
        } for ev in evidence_records
    ]

