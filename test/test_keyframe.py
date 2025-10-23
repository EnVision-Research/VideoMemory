from langchain.agents import create_agent

from src.tools import nano_banana_replicate_tool, update_memory_bank
from src.prompts import KEYFRAME


def test_keyframe():
    thread_id = "FronzenII"
    base_path = f"output/{thread_id}"
    storyboard_path = f"{base_path}/storyboard.json"

    with open(storyboard_path, "r") as f:
        storyboard = f.read()

    keyframe_agent = create_agent(
        model="deepseek:deepseek-chat",
        tools=[nano_banana_replicate_tool, update_memory_bank],
        system_prompt=KEYFRAME,
    )

    query = f"""
    The base path is: {base_path}.
    The storyboard is: {storyboard}.
    """

    for msgs in keyframe_agent.stream(
        input={"messages": [("user", query)]}, 
        stream_mode="values", 
        config={"recursion_limit": 200}
    ):
        msgs['messages'][-1].pretty_print()

if __name__ == "__main__":
    test_keyframe()
