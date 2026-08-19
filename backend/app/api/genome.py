from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.db.session import get_db
from app.db.models.genome_models import GenomeSnapshot

router = APIRouter()

@router.get("")
async def get_genome(company_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(GenomeSnapshot)
        .where(GenomeSnapshot.company_id == company_id)
        .order_by(desc(GenomeSnapshot.created_at))
        .limit(1)
    )
    latest = result.scalar_one_or_none()
    
    if not latest:
        return {"genome": None}
        
    return {
        "id": latest.id,
        "created_at": latest.created_at,
        "traits": latest.traits
    }

@router.get("/history")
async def get_genome_history(company_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(GenomeSnapshot)
        .where(GenomeSnapshot.company_id == company_id)
        .order_by(GenomeSnapshot.created_at)
    )
    history = result.scalars().all()
    
    return [
        {
            "id": h.id,
            "created_at": h.created_at,
            "traits": h.traits
        } for h in history
    ]

