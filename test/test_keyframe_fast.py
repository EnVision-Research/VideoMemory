"""
Fast keyframe planning test.
Single agent processes entire storyboard and outputs complete memory_bank JSON.
No tools needed - pure LLM output.
Actual image generation happens later via batch_generate_images.py.
"""

import json
import logging
import re
from pathlib import Path
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI

from src.prompts import KEYFRAME_FAST_AGENT


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_keyframe_fast():
    """
    Fast keyframe planning: single LLM call outputs complete memory_bank JSON.
    No tools, no agents - just pure LLM output.
    """
    
    thread_id = "Sunflower"
    base_path = f"output/{thread_id}"
    storyboard_path = f"{base_path}/storyboard.json"
    memory_bank_path = Path(base_path) / "memory_bank.json"
    
    # Load storyboard
    logger.info(f"Loading storyboard from {storyboard_path}")
    with open(storyboard_path, "r") as f:
        storyboard = json.load(f)
    
    # Create LLM (no tools, no agents)
    logger.info("Creating LLM")
    llm = ChatOpenAI(
        model="deepseek-chat",
        temperature=0.7,
        max_tokens=16000
    )
    
    # Prepare messages
    messages = [
        {"role": "system", "content": KEYFRAME_FAST_AGENT},
        {"role": "user", "content": f"""Base path: {base_path}

Process this storyboard and output the complete memory_bank JSON:

{json.dumps(storyboard, indent=2)}"""}
    ]
    
    # Execute
    logger.info(f"Starting fast keyframe planning for: {thread_id}")
    logger.info("=" * 80)
    
    response = llm.invoke(messages)
    output_text = response.content
    
    logger.info("LLM output received")
    logger.info("=" * 80)
    
    # Parse JSON from output (strip markdown code blocks if present)
    json_text = output_text.strip()
    if json_text.startswith("```"):
        # Remove markdown code blocks
        json_text = re.sub(r'^```(?:json)?\s*\n', '', json_text)
        json_text = re.sub(r'\n```\s*$', '', json_text)
    
    try:
        memory_bank = json.loads(json_text)
        logger.info("✅ Successfully parsed JSON output")
    except json.JSONDecodeError as e:
        logger.error(f"❌ Failed to parse JSON: {e}")
        logger.error(f"Output text (first 500 chars): {output_text[:500]}")
        raise
    
    # Save to file
    memory_bank_path.parent.mkdir(parents=True, exist_ok=True)
    with open(memory_bank_path, "w") as f:
        json.dump(memory_bank, f, ensure_ascii=False, indent=2)
    
    logger.info(f"💾 Saved to: {memory_bank_path}")
    
    # Count unique assets
    unique_chars = set()
    unique_scenes = set()
    unique_props = set()
    
    for shot in memory_bank["shots"]:
        for char in shot.get("characters", []):
            unique_chars.add(char["name"])
        for scene in shot.get("scenes", []):
            unique_scenes.add(scene["name"])
        for prop in shot.get("props", []):
            unique_props.add(prop["name"])
    
    logger.info(f"\n📊 Summary:")
    logger.info(f"  - Total shots: {len(memory_bank['shots'])}")
    logger.info(f"  - Unique characters: {len(unique_chars)}")
    logger.info(f"  - Unique scenes: {len(unique_scenes)}")
    logger.info(f"  - Unique props: {len(unique_props)}")
    logger.info(f"  - Memory bank: {memory_bank_path}")


if __name__ == "__main__":
    test_keyframe_fast()

