"""
Test cinetography node with parallel video generation and concatenation
"""
from dotenv import load_dotenv
load_dotenv()

from src.graph import cinetography_graph

import asyncio
import logging

# Configure logging format
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_cinetography():

    thread_id = "NeonAegis"
    storyboard_path = f"output/{thread_id}/storyboard.json"
    memory_bank_path = f"output/{thread_id}/memory_bank.json"

    with open(storyboard_path, "r") as f:
        storyboard = f.read()

    with open(memory_bank_path, "r") as f:
        memory_bank = f.read()

    input = {
        "messages": [("user", storyboard)],
        "storyboard": storyboard,
        "memory_bank": memory_bank
    }

    config = {
        "configurable": {"thread_id": thread_id},
    }

    async for msgs in cinetography_graph.astream(input=input, stream_mode="values", config=config):
        msgs['messages'][-1].pretty_print()


if __name__ == "__main__":
    asyncio.run(test_cinetography())