import logging
from langgraph.graph import StateGraph, END
from app.agent.state import WebDNAAgentState
from app.agent.nodes import assess_evidence, execute_tool, generate_interpretation, should_continue

logger = logging.getLogger(__name__)

def build_investigation_graph() -> StateGraph:
    """Builds and compiles the LangGraph investigation agent."""
    
    workflow = StateGraph(WebDNAAgentState)
    
    # Add nodes
    workflow.add_node("assess_evidence", assess_evidence)
    workflow.add_node("execute_tool", execute_tool)
    workflow.add_node("generate_interpretation", generate_interpretation)
    
    # Define edges
    workflow.set_entry_point("assess_evidence")
    
    workflow.add_conditional_edges(
        "assess_evidence",
        should_continue,
        {
            "generate_interpretation": "generate_interpretation",
            "execute_tool": "execute_tool"
        }
    )
    
    workflow.add_edge("execute_tool", "assess_evidence")
    workflow.add_edge("generate_interpretation", END)
    
    return workflow.compile()

agent_graph = build_investigation_graph()

async def run_investigation(
    agent_run_id: str,
    company_id: str, 
    mutation_id: str,
    current_genome: dict,
    previous_genome: dict,
    mutation: dict,
    evidence: list
):
    """Entry point to run the compiled graph."""
    logger.info(f"Starting LangGraph investigation for mutation {mutation_id}")
    
    initial_state = {
        "company_id": company_id,
        "mutation_id": mutation_id,
        "current_genome": current_genome,
        "previous_genome": previous_genome,
        "mutation": mutation,
        "evidence": evidence,
        "evidence_gaps": [],
        "investigation_history": [],
        "tools_called": [],
        "scraper_status": {},
        "evidence_sufficient": False,
        "final_analysis": None,
        "status": "started",
        "step_count": 0,
        "agent_run_id": agent_run_id
    }
    
    config = {"recursion_limit": 15}
    
    try:
        final_state = await agent_graph.ainvoke(initial_state, config=config)
        return final_state
    except Exception as e:
        logger.error(f"Graph execution failed: {e}")
        return None
