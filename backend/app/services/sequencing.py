import asyncio
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.core import SequenceJob, Company
from app.db.models.evidence_models import Source, RawSnapshot
from app.brightdata.client import bright_data_client
from sqlalchemy import select

logger = logging.getLogger(__name__)

async def run_sequence_job(job_id: str, company_id: str, db: AsyncSession):
    try:
        # Load Job
        job = await db.get(SequenceJob, job_id)
        if not job:
            logger.error(f"Job {job_id} not found")
            return

        job.status = "running"
        await db.commit()

        # Load Company
        company = await db.get(Company, company_id)
        if not company:
            job.status = "failed"
            await db.commit()
            return

        # Load Active Sources
        result = await db.execute(select(Source).where(Source.company_id == company_id, Source.is_active == True))
        sources = result.scalars().all()

        job.status = "collecting"
        await db.commit()

        # We need a fallback or fake source if none exist yet for testing Phase 1
        if not sources:
            # Create a mock source for NVIDIA Careers if company is NVIDIA
            if company.name.lower() == "nvidia":
                mock_source = Source(company_id=company.id, type="careers", url="https://nvidia.com/careers", collector_id="mock_careers_collector")
                db.add(mock_source)
                await db.commit()
                sources = [mock_source]
            else:
                job.status = "completed"
                await db.commit()
                return

        # Trigger Bright Data Collectors
        for source in sources:
            logger.info(f"Using Bright Data SERP search for {source.url}")
            try:
                # We map the source to a search query for Bright Data SERP API
                query = f"{company.name} "
                if source.type == "careers":
                    query += "careers jobs"
                elif source.type == "products":
                    query += "products services"
                else:
                    query += "news updates"

                # Run REAL Bright Data search!
                organic_results = await bright_data_client.search(query)
                
                raw_data = []
                for item in organic_results:
                    if source.type == "careers":
                        raw_data.append({"job_title": item.get("title"), "skills": [item.get("description")], "url": item.get("link")})
                    elif source.type == "products":
                        raw_data.append({"product_name": item.get("title"), "description": item.get("description"), "url": item.get("link")})
                    else:
                        raw_data.append({"title": item.get("title"), "summary": item.get("description"), "url": item.get("link")})
                
                # Store raw snapshot
                snapshot = RawSnapshot(
                    company_id=company_id,
                    collector_id=source.collector_id,
                    run_id=f"serp_search_{job.id}",
                    status="completed",
                    raw_data=raw_data
                )
                db.add(snapshot)
                await db.commit()
                
                # Normalize to Evidence
                from app.evidence.normalizer import normalize_snapshot
                job.status = "normalizing"
                await db.commit()
                
                evidences = normalize_snapshot(snapshot, source.type)
                for ev in evidences:
                    db.add(ev)
                await db.commit()
                
            except Exception as e:
                import traceback
                logger.error(f"Failed to collect for {source.url}: {str(e)}\n{traceback.format_exc()}")
                # We should track partial failures, for now we just log

        # Build Genome
        job.status = "building_genome"
        await db.commit()
        from app.genome.builder import build_genome_for_company
        current_genome = await build_genome_for_company(company_id, job.id, db)
        
        # Detect Mutations
        job.status = "detecting_mutations"
        await db.commit()
        from app.genome.mutation import detect_mutations_for_company
        mutations = await detect_mutations_for_company(company_id, job.id, current_genome, db)
        
        # Trigger Agent for severe mutations
        from app.agent.trigger import trigger_agent_investigation
        for mut in mutations:
            if mut.severity in ["high", "critical", "medium"]: # Included medium for better testing
                logger.info(f"Triggering agent for mutation {mut.id} ({mut.severity})")
                await trigger_agent_investigation(mut.id, company_id, db)

        job.status = "completed"
        await db.commit()





    except Exception as e:
        logger.error(f"Sequence job {job_id} failed: {str(e)}")
        # Attempt to mark job as failed
        try:
            job = await db.get(SequenceJob, job_id)
            if job:
                job.status = "failed"
                await db.commit()
        except:
            pass

