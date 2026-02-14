# Questions for GLM/MLX Setup

## How is the GLM Model Currently Served Locally?

The asset-monitor pipeline is working for RSS feeds and market data (successfully fetching 8 equity ETFs), but insights generation is failing because the code tries to call `glm4-cli` which isn't installed.

Looking at the `.env` file: `GLM_MODEL_PATH=/Users/studio/models/hf-cache/models--Qwen/Qwen2.5-0.5B-Instruct`

**Questions:**

1. How is the GLM model (or Qwen2.5-0.5B-Instruct as configured in .env) being served locally with MLX?

2. What endpoint/port/protocol is currently exposed for inference? For example:
   - Is there a local HTTP server running (e.g., `http://localhost:8000/generate`)?
   - Are you using a custom HTTP endpoint like `http://localhost:8866`?
   - Or is it accessed differently (websocket, subprocess, etc.)?

3. Are there any specific installation or running command(s) needed to start the local model server?

4. Does this model need any specific tokenization or configuration when serving it locally?

**Context:** The `LocalGLMAgent` class in `/Users/studio/answerlayer/asset-monitor/app/insight_generator.py` currently tries to call `glm4-cli` via subprocess. We need to modify it to connect to your local MLX model instead.