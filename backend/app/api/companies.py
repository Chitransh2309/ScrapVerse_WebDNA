import logging
from typing import Optional
from urllib.parse import urlparse
from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import AsyncSessionLocal, get_db
from app.db.models.core import Company
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter()

class CompanyCreate(BaseModel):
    name: str
    domain: Optional[str] = None

from app.db.models.evidence_models import Source
from app.db.models.scraper_models import ScraperHealth


def _provision_sources(db_company_id: str, company_name: str, domain: str) -> list[Source]:
    return [
        Source(
            company_id=db_company_id,
            type=src_type,
            url=f"https://{domain}/{src_type}",
            collector_id=f"serp_{src_type}_{company_name.lower().replace(' ', '_')}"
        )
        for src_type in ["careers", "products", "news"]
    ]


def _provision_scraper_health(db_company_id: str, company_name: str) -> list[ScraperHealth]:
    slug = company_name.lower().replace(' ', '_')
    return [
        ScraperHealth(
            company_id=db_company_id,
            collector_id=f"serp_{src_type}_{slug}",
            name=f"{src_type.capitalize()} Collector",
            status="healthy"
        )
        for src_type in ["careers", "products", "news"]
    ]


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


async def _finalize_domain_and_sources(company_id: str, company_name: str):
    """Background task: resolve the real domain and provision sources without
    blocking the create-company response on an external search call."""
    domain = await resolve_domain(company_name)
    async with AsyncSessionLocal() as db:
        try:
            db_company = await db.get(Company, company_id)
            if not db_company:
                return
            db_company.domain = domain
            for src in _provision_sources(company_id, company_name, domain):
                db.add(src)
            for sh in _provision_scraper_health(company_id, company_name):
                db.add(sh)
            await db.commit()
        except Exception as e:
            logger.error(f"Failed to finalize domain/sources for '{company_name}': {e}")
            await db.rollback()


@router.post("")
async def create_company(company: CompanyCreate, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    if company.domain:
        # Domain was given explicitly - no need to resolve or defer anything.
        db_company = Company(name=company.name, domain=company.domain)
        db.add(db_company)
        await db.commit()
        for src in _provision_sources(db_company.id, company.name, company.domain):
            db.add(src)
        for sh in _provision_scraper_health(db_company.id, company.name):
            db.add(sh)
        await db.commit()
        return {"id": db_company.id, "name": db_company.name, "domain": db_company.domain}

    # No domain given: create the company immediately with a placeholder guess
    # so the request returns fast, then resolve the real domain (and sources)
    # in the background - resolving it via search takes several seconds.
    placeholder_domain = company.name.lower().replace(" ", "") + ".com"
    db_company = Company(name=company.name, domain=placeholder_domain)
    db.add(db_company)
    await db.commit()

    background_tasks.add_task(_finalize_domain_and_sources, db_company.id, company.name)

    return {"id": db_company.id, "name": db_company.name, "domain": db_company.domain, "domain_pending": True}

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

