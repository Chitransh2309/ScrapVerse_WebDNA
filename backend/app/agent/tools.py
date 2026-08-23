import logging
import asyncio
from langchain_core.tools import tool
from typing import Dict, Any, List
from app.brightdata.client import bright_data_client
from app.db.session import AsyncSessionLocal

logger = logging.getLogger(__name__)

# To use DB async in tools, we need to run them carefully since tools can be sync or async.
# We will define async tools.

@tool
async def run_products_collector(company_domain: str) -> Dict[str, Any]:
    """Runs a Bright Data search to find new structural product evidence."""
    logger.info(f"Running products search for {company_domain}")
    try:
        results = await bright_data_client.search(f"{company_domain} new products OR features OR launch")
        return {"status": "success", "records_found": len(results), "results": results[:5]}
    except Exception as e:
        return {"status": "error", "error": str(e)}

@tool
async def run_careers_collector(company_domain: str) -> Dict[str, Any]:
    """Runs a Bright Data search to find new hiring signals."""
    logger.info(f"Running careers search for {company_domain}")
    try:
        results = await bright_data_client.search(f"{company_domain} careers hiring jobs")
        return {"status": "success", "records_found": len(results), "results": results[:5]}
    except Exception as e:
        return {"status": "error", "error": str(e)}

@tool
async def run_news_collector(company_domain: str) -> Dict[str, Any]:
    """Runs a Bright Data search to find new announcement evidence."""
    logger.info(f"Running news search for {company_domain}")
    try:
        results = await bright_data_client.search(f"{company_domain} news announcement")
        return {"status": "success", "records_found": len(results), "results": results[:5]}
    except Exception as e:
        return {"status": "error", "error": str(e)}

@tool
async def request_scraper_healing(collector_id: str) -> Dict[str, Any]:
    """Requests Bright Data self-healing workflow for a failed collector."""
    logger.info(f"Requesting self-healing for {collector_id}")
    try:
        out = await bright_data_client.request_self_healing(collector_id)
        return {"status": "healing_requested", "response": out}
    except Exception as e:
        return {"status": "error", "error": str(e)}

TOOLS = [
    run_products_collector,
    run_careers_collector,
    run_news_collector,
    request_scraper_healing
]
