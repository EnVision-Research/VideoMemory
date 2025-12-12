from dotenv import load_dotenv
load_dotenv()

from src.agents import visualization_graph
from src.state import VideoMemoryContext

thread_id = "1"

# Load storyboard and memory_bank from previous pipeline stages
with open(f"output/{thread_id}/storyboard.json", "r") as f:
    storyboard = f.read()

with open(f"output/{thread_id}/memory_bank.json", "r") as f:
    memory_bank = f.read()

config = {
    "configurable": {"thread_id": thread_id},
    "recursion_limit": 50,
}

# Input includes both storyboard and memory_bank in state
input = {
    "messages": [("user", storyboard)],
    "storyboard": storyboard,
    "memory_bank": memory_bank,
}

context = VideoMemoryContext()

async def run_visualization_agent():
    """
    Run the visualization agent to generate keyframes and video clips.
    Use stream_mode="updates" with subgraphs=True to see tool calls from nested agents.
    Uses message.pretty_print() for formatted output.
    """
    async for namespace, chunk in visualization_graph.astream(
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
    asyncio.run(run_visualization_agent())
