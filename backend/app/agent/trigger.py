import logging
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.agent_models import AgentRun
from app.db.models.core import Company
from app.db.models.mutation_models import MutationCandidate
from app.db.models.evidence_models import Evidence
from app.db.models.genome_models import GenomeSnapshot
from sqlalchemy import select, desc
import json

logger = logging.getLogger(__name__)

async def trigger_agent_investigation(mutation_id: str, company_id: str, db: AsyncSession):
    # 1. Fetch Mutation
    mutation = await db.get(MutationCandidate, mutation_id)
    if not mutation:
        return

    company = await db.get(Company, company_id)
    company_domain = company.domain if company else "example.com"
        
    mutation.investigation_status = "investigating"
    await db.commit()
    
    # 2. Create Agent Run
    agent_run = AgentRun(
        company_id=company_id,
        mutation_id=mutation_id,
        status="running"
    )
    db.add(agent_run)
    await db.commit()
    
    # 3. Gather Context (Genomes and Evidence)
    result = await db.execute(
        select(GenomeSnapshot)
        .where(GenomeSnapshot.company_id == company_id)
        .order_by(desc(GenomeSnapshot.created_at))
        .limit(2)
    )
    genomes = result.scalars().all()
    current_genome = genomes[0].traits if len(genomes) > 0 else {}
    previous_genome = genomes[1].traits if len(genomes) > 1 else {}
    
    ev_result = await db.execute(select(Evidence).where(Evidence.id.in_(mutation.evidence_ids)))
    evidence = ev_result.scalars().all()
    
    evidence_dicts = [
        {"id": ev.id, "trait": ev.trait, "type": ev.type, "title": ev.title, "content": ev.content, "confidence": ev.confidence}
        for ev in evidence
    ]
    
    mutation_dict = {
        "trait": mutation.trait,
        "delta": mutation.delta,
        "percentage_change": mutation.percentage_change,
        "severity": mutation.severity,
        "mutation_type": mutation.mutation_type
    }
    
    # 4. Execute Graph
    from app.agent.graph import run_investigation
    final_state = await run_investigation(
        agent_run.id,
        company_id,
        mutation_id,
        current_genome,
        previous_genome,
        mutation_dict,
        evidence_dicts,
        company_domain
    )
    
    # 5. Save Results
    if final_state and final_state.get("final_analysis"):
        mutation = await db.get(MutationCandidate, mutation_id)
        mutation.investigation_status = "completed"
        mutation.final_explanation = final_state["final_analysis"]
        
        agent_run = await db.get(AgentRun, agent_run.id)
        agent_run.status = "completed"
        agent_run.final_result = final_state["final_analysis"]
        agent_run.step_count = final_state.get("step_count", 0)
        
        from datetime import datetime
        agent_run.completed_at = datetime.utcnow()
        
        await db.commit()
    else:
        mutation = await db.get(MutationCandidate, mutation_id)
        mutation.investigation_status = "failed"
        agent_run = await db.get(AgentRun, agent_run.id)
        agent_run.status = "failed"
        await db.commit()
