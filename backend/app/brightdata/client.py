import os
import json
import logging
from typing import Dict, Any, List
from urllib.parse import quote
import httpx

logger = logging.getLogger(__name__)

BRIGHT_DATA_API_KEY = os.getenv("BRIGHT_DATA_API_KEY")
BRIGHT_DATA_SERP_ZONE = os.getenv("BRIGHT_DATA_SERP_ZONE", "serp_api1")
BRIGHT_DATA_API_BASE = "https://api.brightdata.com"


class BrightDataClient:
    async def search(self, query: str) -> List[Dict[str, Any]]:
        """Uses Bright Data's SERP/Web Unlocker API to search Google and return organic results."""
        if not BRIGHT_DATA_API_KEY:
            raise RuntimeError("BRIGHT_DATA_API_KEY is not configured")

        target_url = f"https://www.google.com/search?q={quote(query)}"

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                f"{BRIGHT_DATA_API_BASE}/request",
                headers={"Authorization": f"Bearer {BRIGHT_DATA_API_KEY}"},
                json={"zone": BRIGHT_DATA_SERP_ZONE, "url": target_url, "format": "json"},
            )
            response.raise_for_status()

            try:
                envelope = response.json()
                # api.brightdata.com/request wraps the actual page response in an
                # envelope; the parsed SERP JSON is a JSON *string* inside "body".
                body = json.loads(envelope["body"])
            except (ValueError, KeyError, TypeError):
                logger.error("Failed to parse Bright Data search response")
                return []

            return body.get("organic", [])

    async def request_self_healing(self, collector_id: str) -> str:
        # There's no real Bright Data endpoint for this workflow; it's simulated
        # locally for the demo rather than calling out to an external service.
        logger.info(f"Simulating self-healing request for {collector_id}")
        return "healing_requested"

    async def approve_healing(self, collector_id: str) -> str:
        logger.info(f"Simulating healing approval for {collector_id}")
        return "healed"


bright_data_client = BrightDataClient()
