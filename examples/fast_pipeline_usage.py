"""
Example: Fast Keyframe Generation Pipeline Usage

This example demonstrates the two-phase fast pipeline:
1. Generate all prompts in one LLM call
2. Batch generate images from prompts
"""

import json
import logging
from pathlib import Path

# Configure minimal logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def example_fast_pipeline():
    """
    Complete example of the fast pipeline workflow.
    """
    
    project_name = "Sunflower"
    base_path = f"output/{project_name}"
    
    logger.info("="*80)
    logger.info("Fast Keyframe Generation Pipeline Example")
    logger.info("="*80)
    
    # ========================================================================
    # PHASE 1: Prompt Generation (Fast)
    # ========================================================================
    
    logger.info("\n📝 PHASE 1: Generate All Prompts")
    logger.info("-" * 80)
    
    logger.info("Running: python test/test_keyframe_fast.py")
    logger.info("What happens:")
    logger.info("  1. Load storyboard.json")
    logger.info("  2. Fast Agent processes all shots sequentially")
    logger.info("  3. For each shot:")
    logger.info("     - Parse characters/scenes/props from plot")
    logger.info("     - Call generate_character_prompt (pure function)")
    logger.info("     - Call generate_scene_prompt (pure function)")
    logger.info("     - Call generate_prop_prompt (pure function)")
    logger.info("     - Call generate_keyframe_prompt (pure function)")
    logger.info("     - Call update_memory_bank_fast to save")
    logger.info("  4. Save all prompts to memory_bank.json")
    logger.info("\n⏱️  Estimated time: 2-3 minutes")
    logger.info("💰 Cost: ~1 LLM inference call (~50K tokens)")
    
    # Check if prompts were generated
    memory_bank_path = Path(base_path) / "memory_bank.json"
    if memory_bank_path.exists():
        logger.info(f"\n✅ Prompts found at: {memory_bank_path}")
        
        with open(memory_bank_path, "r") as f:
            memory_bank = json.load(f)
        
        total_shots = len(memory_bank["shots"])
        total_chars = sum(len(shot["characters"]) for shot in memory_bank["shots"])
        total_scenes = sum(len(shot["scenes"]) for shot in memory_bank["shots"])
        total_props = sum(len(shot["props"]) for shot in memory_bank["shots"])
        
        logger.info(f"   - Shots: {total_shots}")
        logger.info(f"   - Character prompts: {total_chars}")
        logger.info(f"   - Scene prompts: {total_scenes}")
        logger.info(f"   - Prop prompts: {total_props}")
        logger.info(f"   - Keyframe prompts: {total_shots}")
        
        # Show example prompt
        if total_shots > 0:
            first_keyframe = memory_bank["shots"][0]["keyframe"]
            logger.info(f"\n📄 Example Keyframe Prompt (Shot 1):")
            logger.info(f"   {first_keyframe['generation_prompt'][:150]}...")
    else:
        logger.warning(f"\n⚠️  No memory_bank.json found. Run test_keyframe_fast.py first.")
    
    # ========================================================================
    # PHASE 2: Batch Image Generation
    # ========================================================================
    
    logger.info("\n\n🎨 PHASE 2: Batch Generate Images")
    logger.info("-" * 80)
    
    logger.info("Running: python scripts/batch_generate_images.py output/Sunflower")
    logger.info("What happens:")
    logger.info("  1. Load memory_bank.json")
    logger.info("  2. For each shot:")
    logger.info("     - Generate character images (if not exists)")
    logger.info("     - Generate scene images (if not exists)")
    logger.info("     - Generate prop images (if not exists)")
    logger.info("     - Generate keyframe image (if not exists)")
    logger.info("  3. Skip already-generated images (resumable)")
    logger.info("\n⏱️  Estimated time: 5-10 minutes per shot (depends on API)")
    logger.info("💰 Cost: API calls only (no LLM inference)")
    logger.info("♻️  Resumable: Can interrupt and restart anytime")
    
    # ========================================================================
    # COMPARISON
    # ========================================================================
    
    logger.info("\n\n📊 PERFORMANCE COMPARISON")
    logger.info("-" * 80)
    logger.info("Method          LLM Calls    Planning Time    Cost")
    logger.info("-" * 80)
    logger.info("Supervisor      40+          ~15 min          ~500K tokens")
    logger.info("Fast (new)      1            ~3 min           ~50K tokens")
    logger.info("-" * 80)
    logger.info("Improvement:    40x fewer    5x faster        10x cheaper")
    
    # ========================================================================
    # TIPS
    # ========================================================================
    
    logger.info("\n\n💡 TIPS")
    logger.info("-" * 80)
    logger.info("1. Review prompts in memory_bank.json before generating images")
    logger.info("2. Edit prompts manually if needed (they're just JSON)")
    logger.info("3. Use batch_generate_images.py with different base_path for other projects")
    logger.info("4. Interrupted? Just re-run batch_generate_images.py (it skips existing images)")
    logger.info("5. Want parallel generation? Modify batch_generate_images.py to use ThreadPoolExecutor")
    
    logger.info("\n" + "="*80)
    logger.info("Example Complete!")
    logger.info("="*80 + "\n")


if __name__ == "__main__":
    example_fast_pipeline()

