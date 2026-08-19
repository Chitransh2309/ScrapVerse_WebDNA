from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, JSON
from app.db.session import Base
from datetime import datetime
import uuid

def generate_uuid():
    return str(uuid.uuid4())

class AgentRun(Base):
    __tablename__ = "agent_runs"

    id = Column(String, primary_key=True, default=generate_uuid)
    company_id = Column(String, ForeignKey("companies.id"), index=True)
    mutation_id = Column(String, ForeignKey("mutations.id"), index=True)
    
    status = Column(String, default="running") # running, completed, failed, timeout
    step_count = Column(Integer, default=0)
    final_result = Column(JSON, nullable=True)
    
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

class AgentEvent(Base):
    __tablename__ = "agent_events"

    id = Column(String, primary_key=True, default=generate_uuid)
    agent_run_id = Column(String, ForeignKey("agent_runs.id"), index=True)
    
    event_type = Column(String) # tool_call, assessment, interpretation, etc.
    tool_name = Column(String, nullable=True)
    status = Column(String)
    
    input_summary = Column(String, nullable=True)
    output_summary = Column(String, nullable=True)
    
    timestamp = Column(DateTime, default=datetime.utcnow)
