from sqlalchemy import Column, String, DateTime, Boolean, JSON, Float, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.db.session import Base
from datetime import datetime
import uuid

def generate_uuid():
    return str(uuid.uuid4())

class Source(Base):
    __tablename__ = "sources"

    id = Column(String, primary_key=True, default=generate_uuid)
    company_id = Column(String, ForeignKey("companies.id"))
    type = Column(String) # products, careers, news, positioning
    url = Column(String)
    collector_id = Column(String) # brightdata_collector_id
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class RawSnapshot(Base):
    __tablename__ = "raw_snapshots"

    id = Column(String, primary_key=True, default=generate_uuid)
    company_id = Column(String, ForeignKey("companies.id"))
    collector_id = Column(String)
    run_id = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)
    status = Column(String)
    raw_data = Column(JSON, nullable=True)
    normalized_data = Column(JSON, nullable=True)
    collection_ids = Column(JSON, nullable=True)
    data_mode = Column(String, default="LIVE")
    created_at = Column(DateTime, default=datetime.utcnow)

class Evidence(Base):
    __tablename__ = "evidence"

    id = Column(String, primary_key=True, default=generate_uuid)
    company_id = Column(String, ForeignKey("companies.id"), index=True)
    snapshot_id = Column(String, ForeignKey("raw_snapshots.id"))
    trait = Column(String, index=True)
    type = Column(String) # careers, products, news, positioning
    title = Column(String)
    content = Column(Text)
    url = Column(String)
    source = Column(String)
    confidence = Column(Float, default=0.0)
    observed_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

