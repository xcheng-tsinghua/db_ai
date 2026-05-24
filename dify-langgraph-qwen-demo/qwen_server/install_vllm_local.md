# Local vLLM Installation Guide

This document describes how to set up vLLM locally on your Ubuntu machine (RTX 4090 24GB) using a native Python virtual environment.

> [!WARNING]
> Native installations of vLLM depend heavily on matching your host machine's CUDA driver, PyTorch version, and compiled CUDA binaries. Compatibility is not guaranteed across all environments, which is why Docker deployment (`start_qwen_vllm_docker.sh`) is often preferred for isolation.

---

## 1. Setup a Dedicated Python Environment

We strongly recommend using a dedicated virtual environment (`venv` or `conda`) to avoid package conflicts.

### Option A: Using Conda (Recommended)
```bash
# Create a new environment with Python 3.10
conda create -n vllm python=3.10 -y
conda activate vllm
```

### Option B: Using Python `venv`
```bash
# Create a venv in your home directory or project directory
python3 -m venv venv_vllm
source venv_vllm/bin/activate
```

---

## 2. Install vLLM

Ensure your pip, setuptools, and wheel packages are upgraded first:

```bash
pip install --upgrade pip setuptools wheel
```

Install vLLM (this will pull down matching versions of PyTorch and CUDA dependencies):

```bash
pip install vllm
```

### Check/Upgrade PyTorch to match CUDA
If your system is using CUDA 12.1+, make sure PyTorch uses it:
```bash
pip install torch --index-url https://download.pytorch.org/whl/cu121
```

---

## 3. Verify the Installation

Run a quick Python command to verify that vLLM loads and detects your GPU:

```bash
python3 -c "import vllm; print('vLLM Version:', vllm.__version__)"
```

---

## 4. Run the Qwen Server

Use the included launch script to start the server:

```bash
bash qwen_server/start_qwen_vllm.sh
```

---

## 5. Troubleshooting Common Issues

### Issue 1: CUDA / PyTorch / driver mismatch
* **Symptoms**: `RuntimeError: Found no NVIDIA driver on your system` or `ImportError: libcudart.so`
* **Fix**: Ensure that `nvidia-smi` works. Re-install PyTorch with the correct CUDA version. For example:
  `pip install torch==2.4.0 --index-url https://download.pytorch.org/whl/cu121`
  If you are running CUDA 12.4, verify your vLLM installation matches CUDA 12.4 instructions from the [vLLM documentation](https://docs.vllm.ai/).

### Issue 2: Out of Memory (OOM)
* **Symptoms**: Python crashes with `CUDA out of memory` during startup or inference.
* **Fix**:
  * Ensure the model is quantized. The default `Qwen/Qwen2.5-14B-Instruct-AWQ` fits comfortably on a 24GB RTX 4090.
  * Reduce `--gpu-memory-utilization` (e.g., from `0.90` to `0.85` or `0.80`) in your `.env`.
  * Reduce `--max-model-len` (e.g. from `8192` to `4096`).
  * Reduce `--max-num-seqs` (e.g. to `1` or `2`).
  * **Avoid running 32B or 72B models** as default on a 24GB card unless aggressive quantization (such as 4-bit) is used.

### Issue 3: Slow Model Download
* **Symptoms**: Downloading the model takes hours or times out.
* **Fix**: Use the Hugging Face mirror site for users in regions with restricted access:
  ```bash
  export HF_ENDPOINT=https://hf-mirror.com
  ```

### Issue 4: Hugging Face Access (HF Token)
* **Symptoms**: vLLM crashes saying the repository is private or requires authorization.
* **Fix**: Qwen2.5-14B-Instruct-AWQ does not require gates/tokens. If you use gated models (e.g. LLaMA-3), log in using:
  `huggingface-cli login` or export `HF_TOKEN=your_token` in your shell before starting.

### Issue 5: Port Conflict (Port 8001 already in use)
* **Symptoms**: `OSError: [Errno 98] Address already in use`
* **Fix**: Find the process using port 8001 (`lsof -i :8001`) and terminate it, or change `QWEN_PORT` in your `.env` file (and update `QWEN_BASE_URL` in the FastAPI backend).

### Issue 6: Insufficient Disk Space
* **Symptoms**: Cache folder runs out of disk space during model weights download.
* **Fix**: By default, weights are stored in `~/.cache/huggingface`. If your root partition is small, redirect the cache folder to a secondary SSD partition:
  ```bash
  export HF_HOME=/mnt/large_drive/huggingface_cache
  ```
