from dotenv import load_dotenv
load_dotenv()

from src.agents import storyboard_graph
from src.state import VideoMemoryContext

thread_id = "Animation2D_fight"
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

async def run_storyboard():
    async for msgs in storyboard_graph.astream(input=input, stream_mode="values", config=config, context=context):
        msgs['messages'][-1].pretty_print()

if __name__ == "__main__":
    import asyncio
    asyncio.run(run_storyboard())