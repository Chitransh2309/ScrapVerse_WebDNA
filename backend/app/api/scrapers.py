from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import get_db
from app.db.models.scraper_models import ScraperHealth
from app.brightdata.client import bright_data_client

router = APIRouter()

@router.get("/companies/{company_id}/scrapers")
async def get_scrapers(company_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ScraperHealth).where(ScraperHealth.company_id == company_id))
    scrapers = result.scalars().all()
    
    return [
        {
            "id": s.id,
            "collector_id": s.collector_id,
            "name": s.name,
            "status": s.status,
            "last_run_at": s.last_run_at,
            "error_message": s.error_message
        } for s in scrapers
    ]

@router.post("/scrapers/{collector_id}/heal")
async def heal_scraper(collector_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ScraperHealth).where(ScraperHealth.collector_id == collector_id))
    scraper = result.scalar_one_or_none()
    
    if not scraper:
        return {"error": "Scraper not found"}
        
    scraper.status = "healing_requested"
    await db.commit()
    
    # In a real setup, this might trigger the Bright Data UI creation flow or CLI command
    await bright_data_client.request_self_healing(collector_id)
    
    return {"status": "healing_requested"}

@router.post("/scrapers/{collector_id}/heal/approve")
async def approve_heal(collector_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ScraperHealth).where(ScraperHealth.collector_id == collector_id))
    scraper = result.scalar_one_or_none()
    
    if not scraper:
        return {"error": "Scraper not found"}
        
    scraper.status = "healed" # Optimistic update
    scraper.error_message = None
    await db.commit()
    
    # Trigger Bright Data CLI to approve healing
    await bright_data_client.approve_healing(collector_id)
    
    return {"status": "healed"}

@router.post("/scrapers/{collector_id}/simulate_failure")
async def simulate_failure(collector_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ScraperHealth).where(ScraperHealth.collector_id == collector_id))
    scraper = result.scalar_one_or_none()
    
    if not scraper:
        return {"error": "Scraper not found"}
        
    scraper.status = "failing"
    scraper.error_message = "Target DOM structure changed. Expected <div class='job-list'> but found <ul id='careers-board'>"
    await db.commit()
    
    return {"status": "failing"}

