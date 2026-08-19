import asyncio
import os
import sys

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'backend'))

from app.db.session import AsyncSessionLocal
from app.db.models.core import Company
from app.db.models.scraper_models import ScraperHealth

async def seed():
    async with AsyncSessionLocal() as session:
        # Check if NVIDIA exists
        from sqlalchemy import select
        result = await session.execute(select(Company).where(Company.name == "NVIDIA"))
        existing = result.scalar_one_or_none()
        
        if not existing:
            nvidia = Company(name="NVIDIA", domain="nvidia.com", description="AI and GPU compute leader.")
            session.add(nvidia)
            await session.commit()
            print(f"Seeded company: NVIDIA (ID: {nvidia.id})")
            
            # Seed Scraper Health
            scrapers = [
                ScraperHealth(company_id=nvidia.id, collector_id="c_products_123", name="Products Collector", status="healthy"),
                ScraperHealth(company_id=nvidia.id, collector_id="c_careers_123", name="Careers Collector", status="healthy"),
                ScraperHealth(company_id=nvidia.id, collector_id="c_news_123", name="News Collector", status="healthy")
            ]
            for s in scrapers:
                session.add(s)
                
            # Seed a baseline Genome from yesterday
            from app.db.models.genome_models import GenomeSnapshot
            from app.genome.taxonomy import get_base_genome_vector
            from datetime import datetime, timedelta
            
            base_genome = get_base_genome_vector()
            base_genome["AI Infrastructure"] = 0.95
            base_genome["Data Center"] = 0.80
            base_genome["Robotics"] = 0.05 # Artificially low so it mutates!
            
            yesterday = datetime.utcnow() - timedelta(days=1)
            past_snapshot = GenomeSnapshot(
                company_id=nvidia.id,
                traits=base_genome,
                created_at=yesterday
            )
            session.add(past_snapshot)
            
            await session.commit()
            print("Seeded scraper health and baseline genome records")

        else:
            print(f"NVIDIA already exists (ID: {existing.id})")

if __name__ == "__main__":
    asyncio.run(seed())
