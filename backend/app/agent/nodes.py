import os
import json
import re
import logging
from typing import Dict, Any, Literal
from app.agent.state import WebDNAAgentState
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# Configure Gemma via OpenRouter
llm = ChatOpenAI(
    api_key=os.getenv("LLM_API_KEY"),
    base_url=os.getenv("LLM_BASE_URL"),
    model=os.getenv("LLM_MODEL", "google/gemma-2-9b-it")
)


def _extract_json(content: str) -> dict:
    """Pulls a JSON object out of an LLM response, tolerating markdown code
    fences and any stray text around them (naive slicing broke whenever the
    model's formatting didn't match exactly)."""
    match = re.search(r"\{.*\}", content, re.DOTALL)
    if not match:
        raise ValueError(f"No JSON object found in LLM response: {content!r}")
    return json.loads(match.group(0))

# Structured Output Models
class EvidenceAssessment(BaseModel):
    is_sufficient: bool = Field(description="Is the current evidence sufficient to explain the mutation?")
    evidence_gaps: list[str] = Field(description="List of identified evidence gaps if any")
    recommended_tool: str = Field(description="The name of the tool to run next to fill the gap (e.g. run_products_collector, run_careers_collector, run_news_collector). Empty if sufficient.")
    reasoning: str = Field(description="Brief reasoning for the decision (internal use only)")

class FinalInterpretation(BaseModel):
    summary: str = Field(description="A concise summary of the mutation and its implications")
    what_changed: str = Field(description="Factual description of what changed based on evidence")
    why_it_matters: str = Field(description="Strategic interpretation of why this change matters")
    possible_implication: str = Field(description="Future implications of this mutation")

async def record_agent_event(agent_run_id: str, event_type: str, status: str, input_summary: str, output_summary: str):
    from app.db.session import AsyncSessionLocal
    from app.db.models.agent_models import AgentEvent
    async with AsyncSessionLocal() as session:
        event = AgentEvent(
            agent_run_id=agent_run_id,
            event_type=event_type,
            status=status,
            input_summary=input_summary,
            output_summary=output_summary
        )
        session.add(event)
        await session.commit()

async def assess_evidence(state: WebDNAAgentState) -> Dict[str, Any]:
    logger.info("Assessing evidence...")
    
    prompt = f"""
    You are an autonomous intelligence agent. Your job is to assess if we have enough evidence to explain a company's mutation.
    
    Mutation Trait: {state['mutation']['trait']}
    Delta: {state['mutation']['delta']} ({state['mutation']['percentage_change']}%)
    Severity: {state['mutation']['severity']}
    
    Current Evidence:
    {json.dumps(state['evidence'], indent=2)}
    
    Tools available: run_products_collector, run_careers_collector, run_news_collector.
    
    Determine if the evidence is sufficient. If not, identify gaps and recommend a tool.
    
    Return EXACTLY a JSON object with NO OTHER TEXT or markdown formatting. The JSON must match this structure:
    {{
        "is_sufficient": false,
        "evidence_gaps": ["List of identified evidence gaps if any"],
        "recommended_tool": "The name of the tool to run next, or empty string if sufficient",
        "reasoning": "Brief reasoning for the decision"
    }}
    """
    
    try:
        response = await llm.ainvoke([
            SystemMessage(content="You are a data-driven business intelligence analyst. Output ONLY JSON."),
            HumanMessage(content=prompt)
        ])
        
        data = _extract_json(response.content)
        is_sufficient = data.get("is_sufficient", False)
        evidence_gaps = data.get("evidence_gaps", [])
        # The LLM sometimes reports insufficient evidence but leaves the tool
        # empty; fall back to a default so execute_tool always has a tool to run.
        recommended_tool = data.get("recommended_tool") or "run_news_collector"
    except Exception as e:
        logger.error(f"LLM parsing failed: {e}. Falling back to default.")
        is_sufficient = False
        evidence_gaps = ["Need more generic data"]
        recommended_tool = "run_news_collector"
    
    await record_agent_event(
        state['agent_run_id'], 
        "assessment", 
        "completed", 
        f"Assessing {len(state['evidence'])} evidence items",
        f"Sufficient: {is_sufficient}"
    )
    
    return {
        "evidence_sufficient": is_sufficient,
        "evidence_gaps": evidence_gaps,
        "tools_called": [{"tool": recommended_tool}] if recommended_tool else [],
        "step_count": state["step_count"] + 1
    }

async def execute_tool(state: WebDNAAgentState) -> Dict[str, Any]:
    # Check max steps
    if state["step_count"] >= 8:
        logger.warning("Max steps reached")
        return {"evidence_sufficient": True} # Force complete
        
    tool_to_run = state["tools_called"][-1]["tool"] if state["tools_called"] else None
    if not tool_to_run:
        logger.warning("No tool recommended; ending investigation")
        return {"evidence_sufficient": True}

    logger.info(f"Executing tool: {tool_to_run}")

    await record_agent_event(
        state['agent_run_id'], 
        "tool_call", 
        "running", 
        f"Running tool {tool_to_run}",
        "Waiting for Bright Data..."
    )
    
    from app.agent.tools import run_products_collector, run_careers_collector, run_news_collector
    
    result = {"status": "success", "records_found": 0}
    company_domain = state.get("company_domain") or "example.com"
    
    try:
        if tool_to_run == "run_products_collector":
            result = await run_products_collector.ainvoke({"company_domain": company_domain})
        elif tool_to_run == "run_careers_collector":
            result = await run_careers_collector.ainvoke({"company_domain": company_domain})
        elif tool_to_run == "run_news_collector":
            result = await run_news_collector.ainvoke({"company_domain": company_domain})
    except Exception as e:
        logger.error(f"Tool execution failed: {e}")
        
    await record_agent_event(
        state['agent_run_id'], 
        "tool_call", 
        "completed", 
        f"Ran tool {tool_to_run}",
        f"Result: {result}"
    )
    
    # Mocking new evidence finding
    new_ev = {
        "type": tool_to_run.replace("run_", "").replace("_collector", ""),
        "trait": state["mutation"]["trait"],
        "title": f"New {tool_to_run} finding",
        "confidence": 0.8
    }
    
    return {
        "evidence": state["evidence"] + [new_ev],
        "step_count": state["step_count"] + 1
    }

async def generate_interpretation(state: WebDNAAgentState) -> Dict[str, Any]:
    logger.info("Generating final interpretation...")
    
    prompt = f"""
    Generate a grounded strategic interpretation based ONLY on the provided evidence.
    Do not hallucinate. Do not change the mutation numbers.
    
    Mutation: {state['mutation']['trait']} changed by {state['mutation']['delta']}.
    Evidence:
    {json.dumps(state['evidence'], indent=2)}
    
    Return EXACTLY a JSON object with NO OTHER TEXT or markdown formatting. The JSON must match this structure:
    {{
        "summary": "A concise summary of the mutation and its implications",
        "what_changed": "Factual description of what changed based on evidence",
        "why_it_matters": "Strategic interpretation of why this change matters",
        "possible_implication": "Future implications of this mutation"
    }}
    """
    
    try:
        response = await llm.ainvoke([
            SystemMessage(content="You are a data-driven business intelligence analyst. You output ONLY valid JSON without markdown tags."),
            HumanMessage(content=prompt)
        ])
        
        final_analysis = _extract_json(response.content)
        final_analysis["evidence_references"] = [ev.get("id", "new") for ev in state["evidence"]]
    except Exception as e:
        logger.error(f"Final LLM parsing failed: {e}")
        mutation = state["mutation"]
        direction = "increased" if mutation["delta"] > 0 else "decreased"
        final_analysis = {
            "summary": f"{mutation['trait']} {direction} by {abs(mutation['percentage_change']):.1f}% ({mutation['severity']} severity), but the AI analysis could not be generated for this run.",
            "what_changed": f"{mutation['trait']} {direction} from the previous baseline ({mutation['mutation_type']}).",
            "why_it_matters": "Automated interpretation was unavailable; review the collected evidence directly to assess significance.",
            "possible_implication": "Unknown - re-run the investigation or review evidence manually.",
            "evidence_references": [ev.get("id", "new") for ev in state["evidence"]]
        }
        
    await record_agent_event(
        state['agent_run_id'], 
        "interpretation", 
        "completed", 
        "Generating final grounded report",
        "Report saved"
    )
        
    return {
        "final_analysis": final_analysis,
        "status": "completed",
        "step_count": state["step_count"] + 1
    }

def should_continue(state: WebDNAAgentState) -> Literal["generate_interpretation", "execute_tool"]:
    if state["evidence_sufficient"] or state["step_count"] >= 8:
        return "generate_interpretation"
    return "execute_tool"
