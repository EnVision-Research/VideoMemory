"""
Fast keyframe planning test.
Single LLM call with structured output - no tools, no agents, no JSON parsing.
Actual image generation happens later via batch_generate_images.py.
"""

import json
import logging
from pathlib import Path
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI

from src.prompts import KEYFRAME_FAST_AGENT
from src.schema import MemoryBank


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_keyframe_fast():
    """
    Fast keyframe planning: single LLM call with structured output.
    No tools, no agents, no JSON parsing - Pydantic handles everything.
    """
    
    thread_id = "Sunflower"
    base_path = f"output/{thread_id}"
    storyboard_path = f"{base_path}/storyboard.json"
    memory_bank_path = Path(base_path) / "memory_bank.json"
    
    # Load storyboard
    logger.info(f"Loading storyboard from {storyboard_path}")
    with open(storyboard_path, "r") as f:
        storyboard = json.load(f)
    
    # Create LLM with structured output (like storyboard_node)
    logger.info("Creating LLM with structured output")
    llm = ChatOpenAI(
        model="deepseek-chat",
        temperature=0.7,
        max_tokens=16000
    ).with_structured_output(MemoryBank)
    
    # Prepare messages
    messages = [
        SystemMessage(content=KEYFRAME_FAST_AGENT),
        HumanMessage(content=f"""Base path: {base_path}

Process this storyboard:

{json.dumps(storyboard, indent=2)}""")
    ]
    
    # Execute
    logger.info(f"Starting fast keyframe planning for: {thread_id}")
    logger.info("=" * 80)
    
    result: MemoryBank = llm.invoke(messages)
    
    logger.info("✅ Structured output received")
    logger.info("=" * 80)
    
    # Save to file
    memory_bank_path.parent.mkdir(parents=True, exist_ok=True)
    with open(memory_bank_path, "w") as f:
        f.write(result.model_dump_json(indent=2))
    
    logger.info(f"💾 Saved to: {memory_bank_path}")
    
    # Count unique assets
    unique_chars = set()
    unique_scenes = set()
    unique_props = set()
    
    for shot in result.shots:
        for char in shot.characters:
            unique_chars.add(char.name)
        for scene in shot.scenes:
            unique_scenes.add(scene.name)
        for prop in shot.props:
            unique_props.add(prop.name)
    
    logger.info(f"\n📊 Summary:")
    logger.info(f"  - Total shots: {len(result.shots)}")
    logger.info(f"  - Unique characters: {len(unique_chars)}")
    logger.info(f"  - Unique scenes: {len(unique_scenes)}")
    logger.info(f"  - Unique props: {len(unique_props)}")
    logger.info(f"  - Memory bank: {memory_bank_path}")


if __name__ == "__main__":
    test_keyframe_fast()

