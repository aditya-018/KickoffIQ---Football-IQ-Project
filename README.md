# Kickoff Football-IQ

Kickoff is an AI football handbook for first-time fans. The first application slice includes a React chat UI, a FastAPI API, and deterministic football-rule explanations with SVG pitch diagrams. The mock intelligence layer is intentionally simple so the app can run before the real RAG, embeddings, and LLM providers are connected.

## Project Structure

```text
backend/    FastAPI API and diagram generation
frontend/   React + TypeScript application
```

## Run Locally

Backend:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export LLM_PROVIDER="nvidia"
export NVIDIA_API_KEY="your_nvidia_api_key"
export NVIDIA_MODEL="your_nvidia_model_name"
export NVIDIA_API_BASE_URL="https://api.nvidia.ai"
uvicorn app.main:app --reload --port 8000
```

If `LLM_PROVIDER` is set to `nvidia`, the backend uses NVIDIA Build-compatible endpoints for embeddings and chat completions. If `LLM_PROVIDER` is set to `openai`, it uses the OpenAI SDK. If no provider is configured or no provider credentials are available, the backend falls back to the local BM25 retrieval and answer builder.

Frontend:

```bash
npm install
npm run dev
```

The frontend expects the API at `http://localhost:8000`. You can override it with `VITE_API_BASE_URL`.
