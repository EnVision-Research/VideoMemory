"""
Fast keyframe planning test.
Single LLM call with structured output - no tools, no agents, no JSON parsing.
Actual image generation happens later via batch_generate_images.py.
"""

import json
import logging
from langchain_core.messages import HumanMessage
import asyncio
from src.graph import keyframe_generation_graph    




# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    thread_id = "Vase"
    with open(f"output/{thread_id}/memory_bank.json", "r") as f:
        memory_bank = json.load(f)
    

    config = {
        "configurable": {"thread_id": thread_id},
    }

    input = {
        "messages": HumanMessage(content=f"Process this memory bank: {memory_bank}"),
        "memory_bank": memory_bank
    }

    async for msgs in keyframe_generation_graph.astream(input=input, stream_mode="values", config=config):
        msgs['messages'][-1].pretty_print()

if __name__ == "__main__":      
    asyncio.run(main())

