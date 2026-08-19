import asyncio
import os
import logging
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_openrouter():
    from langchain_openai import ChatOpenAI
    from langchain_core.messages import HumanMessage
    
    api_key = os.getenv("LLM_API_KEY")
    base_url = os.getenv("LLM_BASE_URL")
    model_name = os.getenv("LLM_MODEL", "google/gemma-2-9b-it")
    
    logger.info(f"API KEY prefix: {api_key[:5] if api_key else 'NONE'}")
    logger.info(f"BASE URL: {base_url}")
    logger.info(f"MODEL: {model_name}")
    
    try:
        llm = ChatOpenAI(
            api_key=api_key,
            base_url=base_url,
            model=model_name
        )
        
        logger.info("Sending ping to OpenRouter...")
        response = await llm.ainvoke([HumanMessage(content="Hello! Respond with 'ping'.")])
        logger.info(f"Response: {response.content}")
        print("SUCCESS")
    except Exception as e:
        logger.error(f"Failed to call OpenRouter: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_openrouter())
