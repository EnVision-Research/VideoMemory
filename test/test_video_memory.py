import asyncio
from src.graph import video_memory_graph    


import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def main():
    thread_id = "Vase"
    with open(f"datasets/benchmark/{thread_id}.txt", "r") as f:
        script = f.read()

    config = {
        "configurable": {"thread_id": thread_id},
    }

    input = {
        "messages": [("user", script)]
    }

    async for msgs in video_memory_graph.astream(input=input, stream_mode="values", config=config):
        msgs['messages'][-1].pretty_print()

if __name__ == "__main__":      
    asyncio.run(main())