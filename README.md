# VideoMemory

An AI-powered video production pipeline that transforms raw scripts into structured screenplays, detailed storyboards, and visually consistent keyframe images using LangGraph and advanced AI models.

## Overview

VideoMemory is a complete pre-production automation system that leverages LangGraph to orchestrate three specialized agents:
1. **Screenwriter Agent**: Converts raw narrative text into professionally formatted three-act screenplays
2. **Storyboard Agent**: Transforms screenplays into production-ready storyboards with detailed shot specifications
3. **Keyframe Agent**: Generates visually consistent keyframe images using a memory bank system

The system maintains visual consistency across all generated images through a cumulative memory bank that stores character references, scene environments, and prop assets.

## Features

### 🎬 Screenwriter Agent
- Transforms raw story text into structured three-act screenplays
- Follows industry-standard screenplay formatting conventions
- Supports temporal progression (character aging, location changes)
- Outputs structured JSON with acts, scenes, and shots
- Enforces content safety guidelines (family-friendly, age-appropriate)

### 📋 Storyboard Agent
- Converts screenplays into detailed production storyboards
- Generates comprehensive shot specifications including:
  - Character identification and key props
  - Emotional tone and visual style
  - Music and sound effects design
  - Cinematography notes (camera angles, movements, framing)
- Maintains scene structure from original screenplay

### 🎨 Keyframe Agent
- Generates keyframe images for all storyboard shots
- Maintains visual consistency using a cumulative memory bank
- Automatically creates and reuses visual references:
  - **Character references**: Full-body portraits with consistent appearance
  - **Scene environments**: Location plates without characters
  - **Prop assets**: Individual object references
- Uses Replicate's `google/nano-banana` model for image generation
- Supports multi-image composition for complex shots

### 🎥 Image-to-Video Generation (Optional)
- Convert keyframes to video using Wan2.2-I2V-A14B model via SiliconFlow API
- Maintains consistency from keyframe images
- Supports customizable aspect ratios and negative prompts

## Project Structure

```
VideoMemory/
├── datasets/
│   └── raw_scripts/           # Input raw story scripts
│       ├── DeadPool.txt
│       ├── FronzenII.txt
│       ├── Juno.txt
│       └── TopGunMaverick.txt
├── output/
│   └── {ProjectName}/
│       ├── script.json        # Generated structured screenplay
│       ├── storyboard.json    # Generated storyboard
│       ├── memory_bank.json   # Cumulative visual reference database
│       ├── memory_bank/
│       │   ├── characters/    # Character reference images
│       │   ├── scenes/        # Scene environment images
│       │   └── props/         # Prop reference images
│       └── keyframes/         # Generated keyframe images + metadata
├── src/
│   ├── graph.py              # LangGraph workflow definition
│   ├── llm.py                # LLM model initialization
│   ├── nodes.py              # Agent node implementations
│   ├── prompts.py            # System prompts for each agent
│   ├── schema.py             # Pydantic data models
│   ├── state.py              # Agent state definition
│   ├── configuration.py      # Runtime configuration
│   └── tools/
│       ├── nano_banana.py           # Image generation (Replicate)
│       ├── update_memory_bank.py    # Memory bank management
│       └── Wan22_I2V_A14B.py        # Video generation (SiliconFlow)
├── test/
│   ├── test_keyframe.py             # Keyframe generation tests
│   └── test_screenwriter_storyboard.py  # Script/storyboard tests
├── langgraph.json            # LangGraph configuration
├── pyproject.toml            # Project dependencies
└── README.md

```

## Requirements

- **Python**: >= 3.11
- **Package Manager**: [uv](https://github.com/astral-sh/uv) (recommended for fast dependency management)
- **API Keys**:
  - Google AI API key (for Gemini models)
  - DeepSeek API key (for DeepSeek models)
  - Replicate API token (for image generation)
  - SiliconFlow API key (optional, for video generation)
  - LangSmith API key (optional, for tracing)

## Installation

### 1. Install uv (Python Package Manager)
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2. Clone and Setup
```bash
git clone <repository-url>
cd VideoMemory
uv sync
```

### 3. Configure Environment Variables
```bash
cp env.example .env
```

Edit `.env` and add your API keys:
```bash
# LLM API Keys
GOOGLE_API_KEY=your_google_api_key
DEEPSEEK_API_KEY=your_deepseek_api_key

# Image Generation API
REPLICATE_API_TOKEN=your_replicate_token

# Video Generation API (Optional)
SILICONFLOW_API_KEY=your_siliconflow_key

# Monitoring (Optional)
LANGSMITH_API_KEY=your_langsmith_key
```

## Usage

### Running with LangGraph CLI

The project is configured for LangGraph Studio and CLI:

```bash
# Start LangGraph server
langgraph dev

# Or use LangGraph Studio for visual workflow editing
```

### Running Tests

```bash
# Test screenwriter and storyboard generation
python test/test_screenwriter_storyboard.py

# Test keyframe generation
python test/test_keyframe.py
```

### Programmatic Usage

```python
from src.graph import screenwriter_storyboard_graph
from langchain_core.messages import HumanMessage

# Load your raw script
with open("datasets/raw_scripts/YourScript.txt", "r") as f:
    raw_script = f.read()

# Configure the workflow
config = {
    "configurable": {
        "thread_id": "YourProjectName",
        "screenwriter_model": "google_genai:gemini-2.5-pro",
        "storyboard_model": "google_genai:gemini-2.5-pro",
        "keyframe_model": "deepseek:deepseek-chat"
    }
}

# Run the complete pipeline
result = await screenwriter_storyboard_graph.ainvoke(
    {"messages": [HumanMessage(content=raw_script)]},
    config=config
)

# Access outputs
print(result["script"])       # Structured screenplay JSON
print(result["storyboard"])   # Detailed storyboard JSON
print(result["memory_bank"])  # Visual reference database
```

## Configuration

### Model Selection

Models can be configured in `src/configuration.py` or via runtime config:

- **Screenwriter**: `google_genai:gemini-2.5-pro` (default)
- **Storyboard**: `google_genai:gemini-2.5-pro` (default)
- **Keyframe**: `deepseek:deepseek-chat` (default)

Supported models:
- Google GenAI: `google_genai:gemini-2.5-pro`, `google_genai:gemini-2.5-flash`
- DeepSeek: `deepseek:deepseek-chat`, `deepseek:deepseek-reasoner`

### Prompt Customization

All agent prompts are defined in `src/prompts.py` and can be customized:
- `SCREENWRITER`: Screenplay formatting and structure rules
- `STORYBOARD`: Production design specifications
- `KEYFRAME`: Visual consistency and AIGC prompt engineering rules

### Data Models

Structured outputs use Pydantic models defined in `src/schema.py`:
- `Script`: Acts → Scenes → Shots (with plot content)
- `Storyboard`: Acts → Scenes → Shots (with production details)
- `MemoryBank`: Characters, Scenes, Props, Keyframes

## How It Works

### 1. Screenwriter Agent
Takes raw narrative text and produces a structured screenplay following the three-act structure:
- **Act 1**: Setup and inciting incident (~30% of duration)
- **Act 2**: Rising action and conflict (~40% of duration)
- **Act 3**: Climax and resolution (~30% of duration)

Constraints:
- Total duration: ~48 seconds (8 shots total)
- Maximum 2 characters
- Maximum 3 locations
- Maximum 5 recurring props

### 2. Storyboard Agent
Converts the screenplay into detailed production specifications for each shot:
- Identifies characters and props
- Defines emotional tone and visual style
- Specifies music and sound design
- Provides cinematography notes

### 3. Keyframe Agent
Generates visually consistent keyframe images using a sophisticated workflow:

#### Memory Bank System
- **First Appearance**: Generates reference images for new characters/scenes/props
- **Subsequent Shots**: Reuses existing references for consistency
- **Multi-Image Composition**: Combines character + scene + prop references

#### Image Generation Process
For each shot:
1. Check memory bank for existing references
2. Generate missing visual elements:
   - Characters: Full-body portraits (1:1 aspect ratio)
   - Scenes: Environment plates without people (16:9)
   - Props: Product shots on white background (1:1)
3. Create keyframe using reference images (16:9)
4. Update memory bank with new assets

#### AIGC Prompt Engineering
- Consistent global visual style across all images
- Static frame composition (no camera movements)
- Multi-image combination prompts for complex shots
- Detailed specifications for lighting, mood, and composition

## Output Files

### Generated Assets

For each project (e.g., `TopGunMaverick`):

```
output/TopGunMaverick/
├── script.json              # Structured screenplay
├── storyboard.json          # Production storyboard
├── memory_bank.json         # Complete visual reference database
├── memory_bank/
│   ├── characters/
│   │   ├── MAVERICK.png
│   │   └── ROOSTER.png
│   ├── scenes/
│   │   └── FLIGHT_BRIEFING_ROOM.png
│   └── props/
│       ├── TACTICAL_SCREEN.png
│       └── MISSION_SCHEMATICS.png
└── keyframes/
    ├── 1.png               # Keyframe image for shot 1
    ├── 1.json              # Metadata and generation details
    ├── 2.png
    ├── 2.json
    └── ...
```

### Memory Bank Structure

The `memory_bank.json` file maintains cumulative records:
```json
{
  "characters": {
    "MAVERICK": [{
      "name": "MAVERICK",
      "generation_prompt": "...",
      "image_path": "output/.../MAVERICK.png",
      "reference_image_list": null
    }]
  },
  "scenes": { ... },
  "props": { ... },
  "keyframes": [
    {
      "act": 1,
      "scene": "INT. FLIGHT BRIEFING ROOM - DAY",
      "shot_number": 1,
      "global_shot_number": 1,
      "character_references": {...},
      "scene_references": {...},
      "prop_references": {...},
      "new_character_list": [...],
      "new_scene": {...},
      "new_prop_list": [...],
      "keyframe": {...}
    }
  ]
}
```

## Advanced Features

### Visual Consistency
- Memory bank ensures character appearances remain consistent across shots
- Reference images guide AI generation for all keyframes
- Supports temporal progression (aging, costume changes) through reference + modified prompts

### Multi-Image Composition
Keyframes can combine multiple reference images:
```python
# Example: Combining character + scene + props
references = [
    "characters/MAVERICK.png",
    "characters/ROOSTER.png",
    "scenes/BRIEFING_ROOM.png",
    "props/TACTICAL_SCREEN.png"
]
# → Creates composite keyframe with all elements
```

### Content Safety
Built-in constraints ensure all outputs are family-friendly:
- No minors (all characters 18+)
- No violence or weapons
- No sexual content
- No mature themes

## Tools and APIs

### Image Generation: nano_banana
- **Model**: `google/nano-banana` (Replicate)
- **Features**: Multi-image input support, aspect ratio control
- **Usage**: Character portraits, scene plates, props, keyframes

### Video Generation: Wan2.2-I2V-A14B
- **Provider**: SiliconFlow
- **Input**: Keyframe image + motion prompt
- **Output**: 4-6 second video clips
- **Aspect Ratios**: 1280x720, 720x1280, 960x960

### Memory Bank Management
- **Tool**: `update_memory_bank`
- **Function**: Persists visual references after each keyframe
- **Output**: JSON snapshots for each shot

## Examples

Sample projects included in `datasets/raw_scripts/`:
- **FronzenII**: Fantasy adventure
- **TopGunMaverick**: Action drama
- **Juno**: Coming-of-age story
- **DeadPool**: Superhero comedy

Each can be processed through the complete pipeline to generate screenplays, storyboards, and keyframes.

## Development

### Testing
```bash
# Run specific test
python test/test_screenwriter_storyboard.py

# Or use pytest
uv run pytest test/
```

### LangGraph Studio
Open the project in LangGraph Studio for visual workflow editing and debugging.

### Dependencies
Managed via `pyproject.toml` and `uv.lock`:
- LangChain & LangGraph
- Pydantic for data validation
- Replicate for image generation
- aiofiles for async file operations
- httpx for HTTP requests

## Troubleshooting

### Common Issues

**API Rate Limits**: Keyframe generation may take time due to image generation API limits. Consider adding delays or batching.

**Memory Bank Growth**: The memory bank accumulates all references. For long projects, monitor disk usage in `output/` directories.

**Model Availability**: Ensure your API keys have access to the specified models. Check provider documentation for model availability.

## Contributing

Contributions are welcome! Areas for improvement:
- Additional video generation providers
- Enhanced prompt engineering
- Better visual style transfer
- Temporal consistency for character aging
- Scene transition effects

## License

MIT License - See LICENSE file for details

## Acknowledgments

- LangChain & LangGraph for the orchestration framework
- Google GenAI & DeepSeek for language models
- Replicate for image generation infrastructure
- SiliconFlow for video generation API

