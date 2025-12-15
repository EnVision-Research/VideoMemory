# VideoMemory

> **VideoMemory**: VideoMemory: Toward Consistent Video Generation via Memory Integration

VideoMemory is a multi-agent video generation framework built on LangGraph that automatically transforms screenplay text into coherent video content. By constructing a Visual Memory Bank to maintain consistency of characters, scenes, and props, it enables a high-quality automated video production pipeline.

## 🎯 Key Features

- **Multi-Agent Collaboration**: Three-stage pipeline architecture: Storyboard → Memory → Visualization
- **Visual Memory Bank**: Automatically manages character, scene, and prop assets to ensure cross-shot visual consistency
- **Structured Output**: Strict output control based on Pydantic Schema
- **Flexible Generation Backend**: Supports Replicate (Nano-Banana) for image generation and Sora-2 for video generation

## 📦 Installation

### Requirements

- Python >= 3.11
- [uv](https://github.com/astral-sh/uv) (recommended package manager)

### Setup

```bash
# Clone the repository
git clone https://github.com/your-username/VideoMemory.git
cd VideoMemory

# Create virtual environment and install dependencies using uv
uv sync
source .venv/bin/activate


### Environment Variables

```bash
cp env.example .env
```

Edit the `.env` file with your API keys:

```env
OPENAI_API_KEY=your_openai_api_key

# Generation API
REPLICATE_API_TOKEN=your_replicate_token

# LangSmith (Optional, for tracing)
LANGSMITH_API_KEY=your_langsmith_key
LANGSMITH_TRACING=true
LANGSMITH_PROJECT=VideoMemory
```

## 🚀 Quick Start

### 1. Prepare Scripts

Place screenplay files in the `scripts/` directory following standard screenplay format.

### 2. Run the Pipeline

```bash
source .venv/bin/activate
python main.py
```

### 3. View Outputs

Generated results are saved in `output/{thread_id}/`:

```
output/1/
├── storyboard.json      # Shot-by-shot storyboard
├── memory_bank.json     # Visual asset index
├── memory_bank/
│   ├── chars/           # Character images
│   ├── props/           # Prop images
│   └── scenes/          # Scene images
├── keyframe.json        # Keyframe metadata
├── keyframes/           # Keyframe images
├── video_clips.json     # Video clip metadata
└── videos/              # Generated video clips
```

## 📁 Project Structure

```
VideoMemory/
├── main.py                 # Entry point
├── src/
│   ├── agents.py           # LangGraph definitions
│   ├── nodes.py            # Agent node implementations
│   ├── state.py            # State and Schema definitions
│   ├── prompts.py          # System prompts
│   └── tools/              # Generation tools
├── scripts/                # Input screenplays
├── output/                 # Generated outputs
├── test/                   # Test files
└── pyproject.toml
```

## 📝 Citation

```bibtex
@software{videomemory2025,
  title={VideoMemory: Toward Consistent Video Generation via Memory Integration},
  author={Your Name},
  year={2024},
  url={https://github.com/your-username/VideoMemory}
}
```

## 📄 License

This project is licensed under the **CC BY-NC-SA 4.0** (Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License).

The code is provided for academic research purposes only.

For any questions, please contact jzhou945@connect.hkust-gz.edu.cn
