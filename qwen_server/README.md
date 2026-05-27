# Local Qwen Inference Server (vLLM)

This directory contains the utility scripts and installation instructions for hosting a local Qwen model server using **vLLM**.

---

## 1. Selected Model: Qwen2.5-14B-Instruct-AWQ

For a single **NVIDIA RTX 4090 (24GB VRAM)** GPU:
* **Recommended Model**: `Qwen/Qwen2.5-14B-Instruct-AWQ`
* **Why**: The AWQ (Activation-aware Weight Quantization) 4-bit quantized version of the Qwen2.5-14B model fits comfortably inside ~10GB of VRAM. This leaves ample memory for large context windows (KV cache) and batch sizes, ensuring extremely high serving throughput and stability.
* **Caution on 32B/72B models**: Running 32B or 72B models on a 24GB VRAM card typically causes Out-Of-Memory (OOM) exceptions during multi-turn or concurrent queries unless context length is restricted heavily.
* **Local Offline Serving**: To load model weights locally (e.g. without an internet connection or Hugging Face access), place the files in the directory `data/models/Qwen2.5-14B-Instruct-AWQ` relative to the project root. Both the native startup script (`start_qwen_vllm.sh`) and the Docker-based script (`start_qwen_vllm_docker.sh`) automatically detect local folders, resolve their paths, and mount them into the container environment.

---

## 2. Quick Start Guide

### Step 1: System Checks
Before launching, run the GPU configuration diagnostics:
```bash
bash qwen_server/check_gpu.sh
```

### Step 2: Select Deployment Method

#### Option A: Running with Docker (Recommended)
This method isolates CUDA and python dependencies inside the official vLLM container.
1. Install requirements detailed in `install_nvidia_container_toolkit.md`.
2. Run the Docker launch script:
   ```bash
   bash qwen_server/start_qwen_vllm_docker.sh
   ```

#### Option B: Running Locally (Native Python)
1. Install vLLM inside your environment using `install_vllm_local.md`.
2. Start the local server:
   ```bash
   bash qwen_server/start_qwen_vllm.sh
   ```

---

## 3. Testing Model Connectivity

Use curl or the test Python script to verify the OpenAI-compatible endpoint (running on port `8001` by default).

### Model Listing Check:
```bash
curl -X GET http://localhost:8001/v1/models
```

### Run Python API Test:
Ensure `openai` is installed in your python environment:
```bash
python3 qwen_server/test_qwen_api.py
```

---

## 4. Integration with FastAPI Agent Backend

The FastAPI backend looks up model server connection details in the root `.env` file. Keep these parameters matched:

```env
# Qwen Server Deployment Configuration
QWEN_MODEL_PATH=data/models/Qwen2.5-14B-Instruct-AWQ
QWEN_SERVED_MODEL_NAME=qwen14b
QWEN_HOST=0.0.0.0
QWEN_PORT=8001
QWEN_MAX_MODEL_LEN=8192
QWEN_GPU_MEMORY_UTILIZATION=0.90
QWEN_MAX_NUM_SEQS=2
QWEN_DTYPE=auto
QWEN_API_KEY=EMPTY

# Agent Backend client matching configurations
QWEN_BASE_URL=http://localhost:8001/v1
QWEN_MODEL=qwen14b
QWEN_API_KEY=EMPTY
```

---

## 5. How to Switch Models Later

To use a different model (e.g. `Qwen/Qwen2.5-7B-Instruct` or `Qwen/Qwen2.5-32B-Instruct-AWQ` if you upgrade hardware):
1. Open the root `.env` file.
2. Modify `QWEN_MODEL_PATH` to your new Hugging Face repo name (or absolute path to local model folder).
3. Modify `QWEN_SERVED_MODEL_NAME` and matching `QWEN_MODEL` values.
4. Restart your vLLM server script.

---

## 6. Troubleshooting Summary

See detailed guides in `install_vllm_local.md` for specific troubleshooting details on OOM, port conflicts, CUDA version mismatches, and download rate issues.
