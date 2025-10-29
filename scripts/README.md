# Fast Keyframe Generation Pipeline

This directory contains scripts for the fast keyframe generation workflow.

## Overview

The fast pipeline splits keyframe generation into two phases:

1. **Phase 1: Prompt Generation** (`test_keyframe_fast.py`)
   - Single agent processes entire storyboard
   - Generates all prompts in one pass
   - Stores prompts in `memory_bank.json`
   - **Fast**: Only 1 LLM inference call for entire project

2. **Phase 2: Batch Image Generation** (`batch_generate_images.py`)
   - Reads prompts from `memory_bank.json`
   - Generates all images via API calls
   - Can be run independently, resumed if interrupted

## Usage

### Step 1: Generate Prompts

```bash
cd /path/to/VideoMemory
python test/test_keyframe_fast.py
```

This will:
- Read `output/Sunflower/storyboard.json`
- Generate all character/scene/prop/keyframe prompts
- Save to `output/Sunflower/memory_bank.json`

### Step 2: Generate Images

```bash
python scripts/batch_generate_images.py output/Sunflower
```

This will:
- Read prompts from `output/Sunflower/memory_bank.json`
- Call image generation API for each asset
- Save images to `output/Sunflower/memory_bank/*/`
- Skip already-generated images (resumable)

## Memory Bank Structure (Fast Version)

```json
{
  "shots": [
    {
      "shot_number": 1,
      "act": 1,
      "scene": "EXT. LINA'S BALCONY - MORNING",
      "characters": [
        {
          "name": "LINA_(29_warm_smile_messy_bun)",
          "generation_prompt": "...",
          "image_path": "output/Sunflower/memory_bank/characters/LINA_(...).png",
          "reference_image_list": null
        }
      ],
      "scenes": [...],
      "props": [...],
      "keyframe": {
        "shot_number": 1,
        "generation_prompt": "References: (image1) scene plate, (image2) character, ...",
        "image_path": "output/Sunflower/keyframes/A1_S1_Sh1.png",
        "reference_image_list": [...]
      }
    }
  ]
}
```

## Performance Comparison

| Method | LLM Calls | Total Time* | Use Case |
|--------|-----------|-------------|----------|
| Supervisor (old) | 40+ | ~15 min | Complex coordination |
| Fast (new) | 1 | ~3 min | Batch processing |

*Assuming 8 shots, excluding image generation time

## Benefits

1. **Speed**: 5-10x faster prompt generation
2. **Cost**: Fewer LLM inference calls
3. **Resumable**: Image generation can be interrupted and resumed
4. **Debuggable**: All prompts visible in single JSON file
5. **Parallelizable**: Can batch-generate images in parallel (future)

## Files

- `batch_generate_images.py`: Batch image generator
- `README.md`: This file

