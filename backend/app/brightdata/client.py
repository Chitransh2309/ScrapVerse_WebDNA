import asyncio
import os
import json
import logging
import subprocess
from typing import Dict, Any

logger = logging.getLogger(__name__)

class BrightDataClient:
    async def _run_bdata_cmd(self, *args: str) -> str:
        npx_cmd = "npx.cmd" if os.name == 'nt' else "npx"
        cmd = [npx_cmd, "--yes", "--package", "@brightdata/cli", "bdata"] + list(args)
        logger.info(f"Running Bright Data CLI: {' '.join(cmd)}")
        
        try:
            # Use asyncio.to_thread with subprocess.run to avoid NotImplementedError 
            # with asyncio subprocesses on Windows under certain event loops (like uvicorn's)
            import subprocess
            
            def run_sync():
                return subprocess.run(
                    cmd, 
                    capture_output=True, 
                    text=True, 
                    encoding='utf-8', 
                    errors='replace'
                )
                
            process = await asyncio.to_thread(run_sync)
            
            if process.returncode != 0:
                logger.error(f"bdata error: {process.stderr}")
                raise RuntimeError(f"Bright Data CLI error: {process.stderr}")
                
            return process.stdout.strip()
        except FileNotFoundError:
            logger.error("Node.js/npx not found on system.")
            raise

    async def search(self, query: str) -> list[Dict[str, Any]]:
        """Uses the real Bright Data SERP API to search the web."""
        out = await self._run_bdata_cmd("search", query, "--json")
        try:
            data = json.loads(out)
            return data.get("organic", [])
        except json.JSONDecodeError:
            logger.error("Failed to parse Bright Data search output as JSON")
            return []

    async def request_self_healing(self, collector_id: str) -> str:
        out = await self._run_bdata_cmd("scraper", "heal", collector_id, "--json")
        return out

    async def approve_healing(self, collector_id: str) -> str:
        out = await self._run_bdata_cmd("scraper", "approve", collector_id, "--json")
        return out

bright_data_client = BrightDataClient()
