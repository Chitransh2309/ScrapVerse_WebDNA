from sqlalchemy import Column, String, DateTime, Float, ForeignKey, JSON
from app.db.session import Base
from datetime import datetime
import uuid

def generate_uuid():
    return str(uuid.uuid4())

class MutationCandidate(Base):
    __tablename__ = "mutations"

    id = Column(String, primary_key=True, default=generate_uuid)
    company_id = Column(String, ForeignKey("companies.id"), index=True)
    sequence_job_id = Column(String, ForeignKey("sequence_jobs.id"), nullable=True)
    
    trait = Column(String, index=True)
    old_value = Column(Float)
    new_value = Column(Float)
    delta = Column(Float)
    percentage_change = Column(Float)
    mutation_type = Column(String) # Addition, Expansion, Contraction
    magnitude = Column(Float)
    severity = Column(String) # insignificant, low, medium, high, critical
    confidence = Column(Float)
    
    # Store references to the evidence that caused this mutation
    evidence_ids = Column(JSON, default=list)
    
    # Status of agent investigation
    investigation_status = Column(String, default="pending") # pending, investigating, completed, failed
    final_explanation = Column(JSON, nullable=True) # The LLM's grounded explanation
    
    created_at = Column(DateTime, default=datetime.utcnow)
