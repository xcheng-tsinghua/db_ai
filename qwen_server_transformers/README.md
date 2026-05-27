# Local Qwen Inference Server (Transformers Fallback)

This directory contains a FastAPI wrapper that serves Qwen models using **PyTorch** and **Hugging Face Transformers** directly.

---

## 1. Overview & Fallback Rationale

This server is designed as a **highly compatible fallback** for environments where:
* **vLLM** causes CUDA, torch version, or NVIDIA driver mismatches.
* You need to load weights directly from a local path via native PyTorch.

### Key Characteristics:
* **Engine**: Native Hugging Face Transformers (`AutoModelForCausalLM`).
* **Defaults**: Uses `Qwen2.5-7B-Instruct` as the default model.
* **Speed**: Slower than vLLM (does not utilize PagedAttention, vLLM continuous batching, etc.), but acts as an excellent, error-resistant choice for development and MVP validation.
* **API Compatibility**: Implements a subset of the OpenAI Chat Completions API (`/v1/chat/completions` and `/v1/models`), meaning the FastAPI/LangGraph backend can switch to it seamlessly with zero code changes.

---

## 2. Installation

Install the required dependencies using the specific requirements file:
```bash
pip install -r qwen_server_transformers/requirements_transformers.txt
```

---

## 3. Configuration

The server configuration resides in your root `.env` file under **Option C**:

```env
# Option C: Transformers direct Qwen2.5-7B-Instruct server
QWEN_BASE_URL=http://127.0.0.1:8001/v1
QWEN_MODEL=qwen7b
QWEN_API_KEY=EMPTY

QWEN_MODEL_PATH=/data/models/Qwen2.5-7B-Instruct
QWEN_SERVED_MODEL_NAME=qwen7b
QWEN_HOST=0.0.0.0
QWEN_PORT=8001
QWEN_DEVICE=cuda
QWEN_DTYPE=auto
QWEN_MAX_NEW_TOKENS=2048
QWEN_TEMPERATURE=0.2
QWEN_TOP_P=0.8
QWEN_REPETITION_PENALTY=1.05
```

Before running, ensure that:
1. The folder `/data/models/Qwen2.5-7B-Instruct` (or your relative path `data/models/Qwen2.5-7B-Instruct`) contains the Qwen model weights and files.
2. A valid `config.json` is present in that directory.

---

## 4. Run the Full Chain

Follow this step-by-step sequence to run and verify the entire system:

### Step 1: Start the Transformers Qwen Server
Launch the model server on port `8001`:
```bash
bash qwen_server_transformers/start_qwen_transformers.sh
```

### Step 2: Test the Qwen Server Connectivity
In a new terminal window, verify that the server is active and returning model listings and completions correctly:
```bash
python qwen_server_transformers/test_transformers_qwen_api.py
```

### Step 3: Start the Agent FastAPI Backend
Run the primary application backend on port `8000`:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
The backend will read the active `.env` file and direct all agent LLM calls to `http://127.0.0.1:8001/v1`.

### Step 4: Test the /agent/invoke Flow
Verify downstream agent workflow execution (LangGraph multi-agent chain) by running the integration test script:
```bash
python scripts/test_agent.py
```
