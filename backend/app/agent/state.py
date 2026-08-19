from typing import TypedDict, List, Dict, Any, Optional
from pydantic import BaseModel

class WebDNAAgentState(TypedDict):
    company_id: str
    mutation_id: str
    
    current_genome: Dict[str, float]
    previous_genome: Dict[str, float]
    
    mutation: Dict[str, Any]
    
    evidence: List[Dict[str, Any]]
    evidence_gaps: List[str]
    
    investigation_history: List[str]
    tools_called: List[Dict[str, Any]]
    
    scraper_status: Dict[str, str]
    
    evidence_sufficient: bool
    
    final_analysis: Optional[Dict[str, Any]]
    status: str
    step_count: int
    agent_run_id: str
