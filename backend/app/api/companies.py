import logging
from typing import Optional
from urllib.parse import urlparse
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import get_db
from app.db.models.core import Company
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter()

class CompanyCreate(BaseModel):
    name: str
    domain: Optional[str] = None

from app.db.models.evidence_models import Source


async def resolve_domain(company_name: str) -> str:
    """Looks up the company's real domain via search instead of guessing <name>.com."""
    fallback = company_name.lower().replace(" ", "") + ".com"
    try:
        from app.brightdata.client import bright_data_client
        results = await bright_data_client.search(f"{company_name} official website")
        for r in results:
            link = r.get("link")
            if not link:
                continue
            netloc = urlparse(link).netloc.removeprefix("www.")
            if netloc:
                return netloc
    except Exception as e:
        logger.warning(f"Domain resolution failed for '{company_name}', falling back to guess: {e}")
    return fallback


@router.post("")
async def create_company(company: CompanyCreate, db: AsyncSession = Depends(get_db)):
    domain = company.domain or await resolve_domain(company.name)

    db_company = Company(name=company.name, domain=domain)
    db.add(db_company)
    await db.commit()

    # Auto-provision sources for the new company
    for src_type in ["careers", "products", "news"]:
        src = Source(
            company_id=db_company.id,
            type=src_type,
            url=f"https://{domain}/{src_type}",
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

