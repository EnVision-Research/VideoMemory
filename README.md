

<div align="center">


# VideoMemory: Toward Consistent Video Generation via Memory Integration

<div style="display: grid; place-items: center;">
<img src="asset/VideoMemorylogo.png" width="50%" alt="Logo">
</div>

<a href="https://hit-perfect.github.io/VideoMemory/"><img src="https://img.shields.io/badge/Project_Page-Online-EA3A97"></a>
<a href="#"><img src="https://img.shields.io/badge/ArXiv-2512.*****-brightgreen"></a> 


[Jinsong Zhou](https://jinsong-zhou.github.io)<sup>1,3*</sup>,
[Yihua Du](https://hit-perfect.github.io)<sup>1*</sup>,
[Xinli Xu](https://scholar.google.com.sg/citations?user=lrgPuBUAAAAJ&hl=zh-CN)<sup>1*†</sup>,
[Luozhou Wang](https://wileewang.github.io)<sup>1</sup>,
Zijie Zhuang<sup>1</sup>,
Yehang Zhang<sup>1</sup>,
Shuaibo Li<sup>1</sup>,
Xiaojun Hu<sup>3</sup>,
Bolan Su<sup>3</sup>,
[Ying-Cong Chen](https://www.yingcong.me)<sup>1,2‡</sup>

<sup>1</sup>HKUST(GZ) &nbsp;&nbsp; <sup>2</sup>HKUST &nbsp;&nbsp; <sup>3</sup>ByteDance

<sup>*</sup>Equal Contribution &nbsp;&nbsp; <sup>†</sup>Project Lead &nbsp;&nbsp; <sup>‡</sup>Corresponding Author

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
@article{zhou2024videomemory,
  title={VideoMemory: Toward Consistent Video Generation via Memory Integration},
  author={Zhou, Jinsong and Du, Yihua and Xu, Xinli and Wang, Luozhou and Zhuang, Zijie and Zhang, Yehang and Li, Shuaibo and Hu, Xiaojun and Su, Bolan and Chen, Ying-Cong},
  journal={arXiv preprint arXiv:2512.*****},
  year={2024}
}
```

# 📄 License

This project is licensed under the **CC BY-NC-SA 4.0** (Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License).

The code is provided for academic research purposes only.

For any questions, please contact jzhou945@connect.hkust-gz.edu.cn
