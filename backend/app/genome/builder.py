from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.models.evidence_models import Evidence
from app.db.models.genome_models import GenomeSnapshot
from app.genome.scorer import score_genome
import logging

logger = logging.getLogger(__name__)

async def build_genome_for_company(company_id: str, job_id: str, db: AsyncSession) -> GenomeSnapshot:
    """
    Gathers all current evidence for a company and generates a new GenomeSnapshot.
    """
    logger.info(f"Building genome for company {company_id} (Job: {job_id})")
    
    # Fetch all evidence for this company up to now
    # Note: For MVP, we're just taking all evidence. In a real system, 
    # we might filter by a time window to let old signals decay.
    result = await db.execute(
        select(Evidence).where(Evidence.company_id == company_id)
    )
    all_evidence = result.scalars().all()
    
    # Generate the deterministic vector
    genome_vector = score_genome(all_evidence)
    
    # Store the snapshot
    genome_snapshot = GenomeSnapshot(
        company_id=company_id,
        sequence_job_id=job_id,
        traits=genome_vector
    )
    
    db.add(genome_snapshot)
    await db.commit()
    
    logger.info(f"Genome generated: {genome_vector}")
    return genome_snapshot
