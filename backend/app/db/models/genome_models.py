from sqlalchemy import Column, String, DateTime, JSON, ForeignKey, Integer
from app.db.session import Base
from datetime import datetime
import uuid

def generate_uuid():
    return str(uuid.uuid4())

class GenomeSnapshot(Base):
    __tablename__ = "genome_snapshots"

    id = Column(String, primary_key=True, default=generate_uuid)
    company_id = Column(String, ForeignKey("companies.id"), index=True)
    sequence_job_id = Column(String, ForeignKey("sequence_jobs.id"), nullable=True)
    
    # Store the deterministic vector as JSON: {"AI Infrastructure": 0.93, "Robotics": 0.12, ...}
    traits = Column(JSON, default=dict)
    
    created_at = Column(DateTime, default=datetime.utcnow)
