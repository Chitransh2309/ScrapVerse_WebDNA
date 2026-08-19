from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import get_db
from app.db.models.core import Company
from pydantic import BaseModel

router = APIRouter()

class CompanyCreate(BaseModel):
    name: str
    domain: str

from app.db.models.evidence_models import Source

@router.post("")
async def create_company(company: CompanyCreate, db: AsyncSession = Depends(get_db)):
    db_company = Company(name=company.name, domain=company.domain)
    db.add(db_company)
    await db.commit()
    
    # Auto-provision sources for the new company
    for src_type in ["careers", "products", "news"]:
        src = Source(
            company_id=db_company.id,
            type=src_type,
            url=f"https://{company.domain}/{src_type}",
            collector_id=f"serp_{src_type}_{company.name.lower().replace(' ', '_')}"
        )
        db.add(src)
    await db.commit()
    
    return {"id": db_company.id, "name": db_company.name, "domain": db_company.domain}

@router.get("")
async def list_companies(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Company))
    companies = result.scalars().all()
    return [{"id": c.id, "name": c.name, "domain": c.domain} for c in companies]

@router.get("/{company_id}")
async def get_company(company_id: str, db: AsyncSession = Depends(get_db)):
    company = await db.get(Company, company_id)
    if not company:
        return {"error": "Not found"}
    return {"id": company.id, "name": company.name, "domain": company.domain}

