# Kickoff Football-IQ Project Status

## What has been done

- Added a working backend FastAPI project with a chat endpoint at `POST /chat`.
- Implemented local law retrieval from `backend/app/data/ifab_laws_seed.json`.
- Added a richer RAG path in `backend/app/services/rag.py`:
  - If `OPENAI_API_KEY` is provided, use OpenAI embeddings and `ChatCompletion`.
  - If OpenAI is unavailable, fallback to BM25-style local retrieval.
- Added dependency support for `openai` in `backend/requirements.txt`.
- Updated `README.md` to document `OPENAI_API_KEY` usage and fallback behavior.
- Verified that the backend import and retrieval pipeline works in a Python 3.11 venv.
- Preserved the existing diagram rendering pipeline in `backend/app/services/diagram.py`.
- Confirmed that the frontend can still connect to `http://localhost:8000` via `VITE_API_BASE_URL`.

## Current state

- The app is a functional prototype with a React frontend and FastAPI backend.
- The backend now supports a real LLM-backed RAG path when configured with OpenAI credentials.
- It also continues to work without OpenAI, using local retrieval and answer formatting.
- The project is not yet fully free-tier because the current LLM path depends on OpenAI.

## Next steps to make it better

### 1. Add provider abstraction and free model support

- Create a provider interface for the LLM and embedding layer.
- Support at least two modes:
  - `openai` (current working path)
  - `local` or `free` using a local/open-source model
- Local options include:
  - Ollama / Llama 3 via a local server
  - `gpt4all` / `llama.cpp` / `localggml` models
  - `sentence-transformers` for embeddings locally
- This will remove the need for an OpenAI API key and make the project truly free-to-run.

### 2. Improve the retrieval pipeline

- Replace the simple BM25 fallback with a proper embedding-based search using local embeddings.
- Add a small vector store or nearest neighbor search using `faiss-cpu` or `scikit-learn`.
- Keep the current `ifab_laws_seed.json` and optionally expand it with more law chunks.

### 3. Strengthen answer generation

- Add a strict prompt that instructs the model to cite retrieved law text.
- Keep the answer friendly and beginner-oriented.
- Add response validation so the system never hallucinates legal rules.

### 4. Add structured scenario extraction

- Build a separate extraction step that converts user questions into structured scenario data.
- Use Pydantic validation for output schema:
  - event type (offside, penalty, throw-in, general)
  - player positions
  - ball position
  - restart type
- Use that structured data to drive diagram rendering more reliably.

### 5. Improve UI and UX

- Add clearer status messaging when the API or diagram is unavailable.
- Show a better prompt on the empty diagram panel.
- Consider a source reference panel for law sections and rule details.

### 6. Add tests and automation

- Add backend unit tests for retrieval, LLM generation, and scenario selection.
- Add frontend tests for chat submission and diagram rendering.
- Add a `tests/` folder and a simple CI workflow if you want a portfolio-quality repository.

### 7. Deploy the app

- Deploy frontend to Vercel or another static host.
- Deploy backend to Render, Fly, or another free hosting service.
- Use environment-based provider selection so live demos can use the free local model or hosted LLM provider.

## Why OpenAI is used today

- The current backend code is wired to the OpenAI Python SDK for both embeddings and chat completion.
- That makes the implementation simple and reliable for a working proof of concept.
- There is no fully free OpenAI model available without an API key.
- OpenAI is used here as a convenience to prove the project as an LLM/RAG example.

## Why you can still make it free

- The project can be made free by switching the LLM layer to an open-source or local model.
- Free model options include:
  - Ollama running locally with a free model
  - `gpt4all` or local GPT-style models
  - local embeddings via `sentence-transformers`
- That change is mostly architectural: replace the OpenAI client calls with a provider-specific adapter.

## Recommended immediate next move

1. Keep the current OpenAI-backed RAG path as a working reference implementation.
2. Add a second `LOCAL_MODEL` mode in backend config.
3. Use `sentence-transformers` for local embeddings and a nearest-neighbor search.
4. Add a simple local model call for answer generation.
5. Deploy a demo and document the provider options in `README.md`.

---

This document is intended to help you close the project quickly while preserving the full-stack RAG story for your profile.