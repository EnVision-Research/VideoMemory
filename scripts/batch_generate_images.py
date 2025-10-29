"""
Batch image generation from memory_bank.json prompts.
Run this after test_keyframe_fast.py completes to generate actual images.
"""

import json
import logging
from pathlib import Path
from src.tools.nano_banana import nano_banana_replicate_tool


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def batch_generate(base_path: str):
    """Generate all images from memory_bank.json prompts"""
    
    memory_bank_path = Path(base_path) / "memory_bank.json"
    
    if not memory_bank_path.exists():
        logger.error(f"Memory bank not found at {memory_bank_path}")
        return
    
    logger.info(f"Loading memory bank from {memory_bank_path}")
    with open(memory_bank_path, "r") as f:
        memory_bank = json.load(f)
    
    total_shots = len(memory_bank["shots"])
    logger.info(f"Found {total_shots} shots to process")
    
    for idx, shot_record in enumerate(memory_bank["shots"], 1):
        shot_num = shot_record["shot_number"]
        logger.info(f"\n{'='*80}")
        logger.info(f"Processing Shot {shot_num} ({idx}/{total_shots})")
        logger.info(f"{'='*80}")
        
        # Generate characters
        for char in shot_record["characters"]:
            image_path = Path(char["image_path"])
            if image_path.exists():
                logger.info(f"  ✓ Character already exists: {char['name']}")
                continue
            
            logger.info(f"  🎭 Generating character: {char['name']}")
            try:
                nano_banana_replicate_tool.invoke({
                    "prompt": char["generation_prompt"],
                    "output_path": str(image_path),
                    "reference_images": char.get("reference_image_list") or [],
                    "aspect_ratio": "1:1"
                })
                logger.info(f"    ✓ Saved to {image_path}")
            except Exception as e:
                logger.error(f"    ✗ Failed: {e}")
        
        # Generate scenes
        for scene in shot_record["scenes"]:
            image_path = Path(scene["image_path"])
            if image_path.exists():
                logger.info(f"  ✓ Scene already exists: {scene['name']}")
                continue
            
            logger.info(f"  🏞️ Generating scene: {scene['name']}")
            try:
                nano_banana_replicate_tool.invoke({
                    "prompt": scene["generation_prompt"],
                    "output_path": str(image_path),
                    "reference_images": [],
                    "aspect_ratio": "16:9"
                })
                logger.info(f"    ✓ Saved to {image_path}")
            except Exception as e:
                logger.error(f"    ✗ Failed: {e}")
        
        # Generate props
        for prop in shot_record["props"]:
            image_path = Path(prop["image_path"])
            if image_path.exists():
                logger.info(f"  ✓ Prop already exists: {prop['name']}")
                continue
            
            logger.info(f"  🔧 Generating prop: {prop['name']}")
            try:
                nano_banana_replicate_tool.invoke({
                    "prompt": prop["generation_prompt"],
                    "output_path": str(image_path),
                    "reference_images": prop.get("reference_image_list") or [],
                    "aspect_ratio": "1:1"
                })
                logger.info(f"    ✓ Saved to {image_path}")
            except Exception as e:
                logger.error(f"    ✗ Failed: {e}")
        
        # Generate keyframe
        keyframe = shot_record["keyframe"]
        image_path = Path(keyframe["image_path"])
        if image_path.exists():
            logger.info(f"  ✓ Keyframe already exists: Shot {keyframe['shot_number']}")
        else:
            logger.info(f"  🎬 Generating keyframe: Shot {keyframe['shot_number']}")
            try:
                nano_banana_replicate_tool.invoke({
                    "prompt": keyframe["generation_prompt"],
                    "output_path": str(image_path),
                    "reference_images": keyframe.get("reference_image_list") or [],
                    "aspect_ratio": "16:9"
                })
                logger.info(f"    ✓ Saved to {image_path}")
            except Exception as e:
                logger.error(f"    ✗ Failed: {e}")
    
    logger.info(f"\n{'='*80}")
    logger.info("✅ Batch generation complete!")
    logger.info(f"{'='*80}")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python scripts/batch_generate_images.py <base_path>")
        print("Example: python scripts/batch_generate_images.py output/Sunflower")
        sys.exit(1)
    
    base_path = sys.argv[1]
    batch_generate(base_path)

