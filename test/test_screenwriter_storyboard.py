import asyncio
from src.graph import screenwriter_storyboard_graph


async def main():
    thread_id = "Harry"
    with open(f"datasets/raw_scripts/{thread_id}.txt", "r") as f:
        script = f.read()

    config = {
        "configurable": {"thread_id": thread_id},
    }

    input = {
        "messages": [("user", script)]
    }

    async for msgs in screenwriter_storyboard_graph.astream(input=input, stream_mode="values", config=config):
        msgs['messages'][-1].pretty_print()

if __name__ == "__main__":      
    asyncio.run(main())