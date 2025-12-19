

<div align="center">


# VideoMemory: Toward Consistent Video Generation via Memory Integration

<a href="https://hit-perfect.github.io/VideoMemory/"><img src="https://img.shields.io/badge/Project_Page-Online-EA3A97"></a>
<a href="#"><img src="https://img.shields.io/badge/ArXiv-2512.*****-brightgreen"></a> 

</div>


Official implementation of VideoMemory: Toward Consistent Video Generation via Memory Integration.

<div style="display: grid; place-items: center;">
<img src="asset/Pipeline.png" width="100%" alt="Framework">
</div>

VideoMemory is a multi-agent video generation framework built on LangGraph that automatically transforms screenplay text into coherent video content. By constructing a Visual Memory Bank to maintain consistency of characters, scenes, and props, it enables a high-quality automated video production pipeline.

# 🚩 Features
- [✅] Multi-Agent Collaboration: Three-stage pipeline architecture (Storyboard → Memory → Visualization)
- [✅] Visual Memory Bank: Automatically manages character, scene, and prop assets to ensure cross-shot visual consistency
- [✅] Structured Output: Strict output control based on Pydantic Schema
- [✅] Flexible Generation Backend: Supports Replicate (Nano-Banana) for image generation and Sora-2 for video generation

# ⚙️ Dependencies and Installation

We recommend using `Python>=3.11` and [uv](https://github.com/astral-sh/uv) package manager.

```bash
# Clone the repository
git clone https://github.com/your-username/VideoMemory.git
cd VideoMemory

# Create virtual environment and install dependencies using uv
uv sync
source .venv/bin/activate
```

## Environment Variables

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

# 💫 Run

## Prepare Scripts

Place screenplay files in the `scripts/` directory following standard screenplay format.

## Run the Pipeline

```bash
source .venv/bin/activate
python main.py
```

# 📚 Citation

If you find this project helpful in your research or applications, please cite it as follows:

```BibTeX
@software{videomemory2025,
  title={VideoMemory: Toward Consistent Video Generation via Memory Integration},
  author={Your Name},
  year={2024},
  url={https://github.com/your-username/VideoMemory}
}
```

# 📄 License

This project is licensed under the **CC BY-NC-SA 4.0** (Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License).

The code is provided for academic research purposes only.

For any questions, please contact jzhou945@connect.hkust-gz.edu.cn
