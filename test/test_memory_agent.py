from dotenv import load_dotenv
load_dotenv()

from src.agents import memory_graph
from src.state import VideoMemoryContext

thread_id = "2"
with open(f"output/{thread_id}/storyboard.json", "r") as f:
    storyboard = f.read()

config = {
    "configurable": {"thread_id": thread_id},
}

input = {
    "messages": [("user", storyboard)]
}

context = VideoMemoryContext()

async def run_memory_agent():
    """
    Use stream_mode="updates" with subgraphs=True to see tool calls from nested agents.
    Uses message.pretty_print() for formatted output.
    """
    async for namespace, chunk in memory_graph.astream(
        input=input, 
        stream_mode="updates",
        subgraphs=True,
        config=config, 
        context=context
    ):
        for node_name, node_output in chunk.items():
            if "messages" in node_output:
                messages = node_output["messages"]
                if not isinstance(messages, list):
                    messages = [messages]
                for msg in messages:
                    msg.pretty_print()

if __name__ == "__main__":
    import asyncio
    asyncio.run(run_memory_agent())