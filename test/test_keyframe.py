"""
Fast keyframe planning test.
Single LLM call with structured output - no tools, no agents, no JSON parsing.
Actual image generation happens later via batch_generate_images.py.
"""

import json
import logging
from langchain_core.messages import SystemMessage, HumanMessage
import asyncio
from src.graph import keyframe_graph    




# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    thread_id = "Sunflower"
    with open(f"output/{thread_id}/storyboard.json", "r") as f:
        storyboard = f.read()
    

    config = {
        "configurable": {"thread_id": thread_id},
    }

    input = {
        "messages": HumanMessage(content=f"Process this storyboard: {storyboard}"),
        "storyboard": storyboard
    }

    async for msgs in keyframe_graph.astream(input=input, stream_mode="values", config=config):
        msgs['messages'][-1].pretty_print()

if __name__ == "__main__":      
    asyncio.run(main())

