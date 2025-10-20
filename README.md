# VideoMemory

A small pipeline that turns a raw script into a structured screenplay (Script), a production-ready storyboard (Storyboard), and finally per-shot keyframes guided by a visual memory bank for character/scene/prop consistency.

### Features
- Screenwriter: transform raw text into a structured three‑act `Script`.
- Storyboard: convert `Script` into shot‑level `Storyboard` with production details.
- Keyframe agent: generate per‑shot keyframes using a memory bank of characters/scenes/props to keep visual continuity.

### Project Structure
```
datasets/
  raw_scripts/
    FronzenII.txt            # example input script
output/
  FronzenII/
    script.json              # generated screenplay
    storyboard.json          # generated storyboard
    memory_bank/             # reference images used by keyframe agent
    keyframes/               # generated keyframes per shot
src/
  configuration.py          # runtime configuration via env or RunnableConfig
  nodes.py                  # screenwriter node (LangChain runnable)
  prompts.py                # prompts for different agents
  schema.py                 # Pydantic models for Script/Storyboard/Keyframe
  state.py                  # shared agent state (if extended)
  tools/nano_banana.py      # image generation tool (Replicate wrapper)
main.py                     # quick test entrypoints for each stage
pyproject.toml              # project + deps (managed by uv)
```

### Requirements
- Python >= 3.11
- uv (Python package/dependency manager)

### Installation
```bash
# 1) Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2) Sync dependencies
uv sync
```

### Environment Variables
Copy `env.example` to `.env` and fill in your keys.
```bash
cp env.example .env
```
Keys required:
- `GOOGLE_API_KEY` (if you use Google GenAI models via LangChain)
- `DEEPSEEK_API_KEY` (for DeepSeek models)
- `REPLICATE_API_TOKEN` (for image generation tool)

### Usage
You can invoke each stage separately using the helpers in `main.py`.

```bash
# Activate uv virtualenv for this project
uv venv
source .venv/bin/activate

# Run keyframe demo by default (edit main.py to enable others)
python main.py
```

The provided `main.py` includes three sample functions:
- `test_screenwriter()` – reads `datasets/raw_scripts/FronzenII.txt`, writes `output/FronzenII/script.json`.
- `test_storyboard()` – reads the saved script and writes `output/FronzenII/storyboard.json`.
- `test_keyframe()` – loads the storyboard, prepares a sample memory bank, and streams keyframe generation via `tools.nano_banana` on Replicate.

Uncomment the desired function in `main.py` under the `if __name__ == "__main__":` guard.

### Models and Prompts
- Models are configured via `src/configuration.py` and environment variables.
- Prompts for different agents live in `src/prompts.py`.
- Pydantic schemas for structured outputs are in `src/schema.py`.

### Outputs
- Script and storyboard JSONs are written under `output/FronzenII/`.
- Keyframes and updated memory bank assets are stored under corresponding subfolders.

### Notes
- This project uses LangChain, LangGraph, and Replicate. Ensure the relevant API keys are set.
- Replace the example dataset/script and memory bank images with your own to adapt the pipeline.

### License
MIT

