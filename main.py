from dotenv import load_dotenv
load_dotenv()

from src.agents import video_memory_graph
from src.state import VideoMemoryContext

import logging
logging.basicConfig(level=logging.INFO)


async def run_video_memory():

    thread_id = "2"
    with open(f"scripts/{thread_id}.txt", "r") as f:
        script = f.read()

    config = {
        "configurable": {"thread_id": thread_id},
        "recursion_limit": 50,
    }

    input = {
        "messages": [("user", script)]
    }

    # 创建上下文实例
    context = VideoMemoryContext()

    async for msgs in video_memory_graph.astream(input=input, stream_mode="values", config=config, context=context):
        msgs['messages'][-1].pretty_print()

if __name__ == "__main__":
    import asyncio
    asyncio.run(run_video_memory())