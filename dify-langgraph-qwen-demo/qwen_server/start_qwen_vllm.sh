#!/usr/bin/env bash

# Exit on error
set -e

# Resolve script directory to load local config if present
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

# 1. Load variables from .env if it exists
if [ -f "$ROOT_DIR/.env" ]; then
    echo "Loading configurations from $ROOT_DIR/.env"
    export $(grep -v '^#' "$ROOT_DIR/.env" | grep -v '^[[:space:]]*$' | xargs)
else
    echo "No .env file found at root, using default values."
fi

# 2. Set safe defaults if environment variables are missing
QWEN_MODEL_PATH=${QWEN_MODEL_PATH:-"Qwen/Qwen2.5-14B-Instruct-AWQ"}
QWEN_SERVED_MODEL_NAME=${QWEN_SERVED_MODEL_NAME:-"qwen14b"}
QWEN_HOST=${QWEN_HOST:-"0.0.0.0"}
QWEN_PORT=${QWEN_PORT:-8001}
QWEN_MAX_MODEL_LEN=${QWEN_MAX_MODEL_LEN:-8192}
QWEN_GPU_MEMORY_UTILIZATION=${QWEN_GPU_MEMORY_UTILIZATION:-0.90}
QWEN_MAX_NUM_SEQS=${QWEN_MAX_NUM_SEQS:-2}
QWEN_DTYPE=${QWEN_DTYPE:-"auto"}
QWEN_API_KEY=${QWEN_API_KEY:-"EMPTY"}

# Warning about 32B or larger models on 24GB GPUs
if [[ "$QWEN_MODEL_PATH" == *"32B"* || "$QWEN_MODEL_PATH" == *"72B"* ]]; then
    echo "========================================= WARNING ========================================="
    echo "You are configuring a model path ($QWEN_MODEL_PATH) that seems larger than 14B."
    echo "Serving 32B or 72B models on a single RTX 4090 (24GB VRAM) may cause Out-Of-Memory (OOM) errors"
    echo "unless aggressive quantization (AWQ/GPTQ/GGUF) or highly restricted context lengths are used."
    echo "We recommend using Qwen2.5-14B-Instruct-AWQ as the default for stability on 24GB GPUs."
    echo "==========================================================================================="
fi

# 3. Check whether Python and vLLM are available
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed or not in PATH."
    exit 1
fi

if ! python3 -c "import vllm" &> /dev/null; then
    echo "Error: vLLM is not installed in the current Python environment."
    echo "Please activate the correct environment or install vLLM locally first."
    echo "See install_vllm_local.md for instructions."
    exit 1
fi

# 4. Print GPU information using nvidia-smi if available
if command -v nvidia-smi &> /dev/null; then
    echo "GPU Information detected:"
    nvidia-smi --query-gpu=name,memory.total,memory.free --format=csv
else
    echo "Warning: nvidia-smi not found. Ensure NVIDIA drivers are installed if running on a GPU."
fi

# 5. Print the final model serving configuration
echo "Starting vLLM OpenAI API Server with configuration:"
echo "--------------------------------------------------------"
echo "Model Path:              $QWEN_MODEL_PATH"
echo "Served Model Name:       $QWEN_SERVED_MODEL_NAME"
echo "Host & Port:             $QWEN_HOST:$QWEN_PORT"
echo "Max Model Len:           $QWEN_MAX_MODEL_LEN"
echo "GPU Memory Util:         $QWEN_GPU_MEMORY_UTILIZATION"
echo "Max Num Sequences:       $QWEN_MAX_NUM_SEQS"
echo "Dtype:                   $QWEN_DTYPE"
echo "--------------------------------------------------------"

# Export API key for vLLM authorization
export VLLM_API_KEY="$QWEN_API_KEY"

# 6. Start vLLM OpenAI-compatible server
exec vllm serve "$QWEN_MODEL_PATH" \
  --host "$QWEN_HOST" \
  --port "$QWEN_PORT" \
  --served-model-name "$QWEN_SERVED_MODEL_NAME" \
  --max-model-len "$QWEN_MAX_MODEL_LEN" \
  --gpu-memory-utilization "$QWEN_GPU_MEMORY_UTILIZATION" \
  --max-num-seqs "$QWEN_MAX_NUM_SEQS" \
  --dtype "$QWEN_DTYPE"
