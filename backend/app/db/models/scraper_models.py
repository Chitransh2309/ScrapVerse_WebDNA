from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, Boolean
from app.db.session import Base
from datetime import datetime
import uuid

def generate_uuid():
    return str(uuid.uuid4())

class ScraperHealth(Base):
    __tablename__ = "scraper_health"

    id = Column(String, primary_key=True, default=generate_uuid)
    company_id = Column(String, ForeignKey("companies.id"), index=True)
    collector_id = Column(String, index=True, unique=True)
    
    name = Column(String) # e.g., "Careers Collector"
    status = Column(String, default="healthy") # healthy, failing, healing_requested, healing_approved, healed
    
    last_run_at = Column(DateTime, nullable=True)
    error_message = Column(String, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
