# Modular AI Agent Base

This project is a model provider-agnostic AI agent base equipped with a FastAPI backend, a LangGraph workflow coordinator, and a React + Vite + TypeScript frontend styled with premium custom Glassmorphism Vanilla CSS. It provides integration with MiniMax, OpenAI-compatible APIs, and local LLMs (like Qwen via Ollama/vLLM) alongside a sandboxed Local File safety Agent.

## Core Features

1.  **Dynamic Provider Routing:** Switch between `minimax`, `openai_compatible`, and `local_qwen` adapters without rewriting business logic.
2.  **Multimodal capabilities:** Text completions, image generation, image-to-image synthesis, and async task queues with status polling for video and music synthesis.
3.  **LangGraph Workflow Trace:** A custom frontend step-by-step execution trace visualizer.
4.  **Safe Local File Agent:** Path traversal guards, dry-runs with plan reviews, unified color-coded diff displays, and timestamped backups in `.agent_backups/`.

---

## Setup & Running

### Prerequisites
*   Anaconda or Miniconda
*   Python 3.11+
*   Node.js 26+ and npm (Installed in Conda environment)

### Environment Configuration
Copy `.env.example` to `.env` in the root folder and add your API keys:
```bash
cp .env.example .env
```

### 1. Run the FastAPI Backend
1.  Activate your conda environment:
    ```bash
    conda activate db_ai
    ```
2.  Ensure backend dependencies are met (most are pre-installed in the `db_ai` environment):
    ```bash
    pip install -r backend/requirements.txt
    ```
3.  Start the FastAPI application server:
    ```bash
    uvicorn backend.app.main:app --reload --port 8001
    ```
4.  Verify the REST API interactive docs are running at: `http://localhost:8001/docs`.

### 2. Run the React Frontend
1.  Open a new terminal, activate the conda environment to use the environment's Node/npm binaries:
    ```bash
    conda activate db_ai
    ```
2.  Navigate to the `frontend/` folder, install Node packages and run the Vite dev server:
    ```bash
    cd frontend
    npm install
    npm run dev
    ```
3.  Open your browser and navigate to `http://localhost:5173`.

---

## Running Verification Tests

Run the backend unit tests to verify provider routing and file agent safety mechanics:
```bash
conda activate db_ai
pytest tests/test_providers.py
pytest tests/test_file_agent.py
```
