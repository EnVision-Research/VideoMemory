"""
Fast keyframe planning test.
Single agent processes entire storyboard and generates all prompts.
Actual image generation happens later via batch_generate_images.py.
"""

import json
import logging
from pathlib import Path
from langchain.agents import create_agent

from src.prompts import KEYFRAME_FAST_AGENT
from src.tools.prompt_generators import (
    generate_character_prompt,
    generate_scene_prompt,
    generate_prop_prompt,
    generate_keyframe_prompt
)
from src.tools.update_memory_bank import update_memory_bank_fast


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_keyframe_fast():
    """
    Fast keyframe planning: single agent processes entire storyboard.
    Generates prompts only - actual image generation happens later.
    """
    
    thread_id = "Sunflower"
    base_path = f"output/{thread_id}"
    storyboard_path = f"{base_path}/storyboard.json"
    
    # Load storyboard
    logger.info(f"Loading storyboard from {storyboard_path}")
    with open(storyboard_path, "r") as f:
        storyboard = json.load(f)
    
    # Create tools (NOT agents - pure functions)
    tools = [
        generate_character_prompt,
        generate_scene_prompt,
        generate_prop_prompt,
        generate_keyframe_prompt,
        update_memory_bank_fast
    ]
    
    # Create single fast agent
    logger.info("Creating fast agent")
    fast_agent = create_agent(
        model="deepseek:deepseek-chat",
        tools=tools,
        system_prompt=KEYFRAME_FAST_AGENT
    )
    
    # Prepare input
    user_message = f"""Base path: {base_path}

Process this storyboard and generate all prompts:

{json.dumps(storyboard, indent=2)}"""
    
    input_data = {
        "messages": [{"role": "user", "content": user_message}]
    }
    
    config = {
        "configurable": {"thread_id": thread_id},
        "recursion_limit": 50  # Much lower than supervisor (only 1 agent)
    }
    
    # Execute
    logger.info(f"Starting fast keyframe planning for: {thread_id}")
    logger.info("=" * 80)
    
    for chunk in fast_agent.stream(
        input=input_data,
        stream_mode="values",
        config=config
    ):
        if "messages" in chunk:
            chunk["messages"][-1].pretty_print()
    
    logger.info("=" * 80)
    logger.info("Prompt generation complete")
    
    # Verify output
    memory_bank_path = Path(base_path) / "memory_bank.json"
    assert memory_bank_path.exists(), "memory_bank.json not created"
    
    with open(memory_bank_path, "r") as f:
        memory_bank = json.load(f)
    
    # Count unique assets
    unique_chars = set()
    unique_scenes = set()
    unique_props = set()
    
    for shot in memory_bank["shots"]:
        for char in shot["characters"]:
            unique_chars.add(char["name"])
        for scene in shot["scenes"]:
            unique_scenes.add(scene["name"])
        for prop in shot["props"]:
            unique_props.add(prop["name"])
    
    logger.info(f"\n📊 Summary:")
    logger.info(f"  - Total shots: {len(memory_bank['shots'])}")
    logger.info(f"  - Unique characters: {len(unique_chars)}")
    logger.info(f"  - Unique scenes: {len(unique_scenes)}")
    logger.info(f"  - Unique props: {len(unique_props)}")
    logger.info(f"  - Memory bank: {memory_bank_path}")


if __name__ == "__main__":
    test_keyframe_fast()

