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

# Set safe defaults
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
    echo "Serving 32B or 72B models on a single RTX 4090 (24GB VRAM) may cause Out-Of-Memory (OOM) errors."
    echo "==========================================================================================="
fi

# 2. Check whether Docker is installed
if ! command -v docker &> /dev/null; then
    echo "Error: Docker is not installed or not in PATH."
    exit 1
fi

# 3. Check whether nvidia-smi is available
if ! command -v nvidia-smi &> /dev/null; then
    echo "Warning: nvidia-smi not found. Docker GPU runtime requires NVIDIA Drivers."
fi

# 4. Check whether Docker can access the GPU
echo "Checking if Docker can access the GPU using nvidia-smi inside a container..."
if ! docker run --rm --gpus all nvidia/cuda:12.0.0-base-ubuntu22.04 nvidia-smi &> /dev/null; then
    echo "Error: Docker does not have GPU access. Please install the NVIDIA Container Toolkit."
    echo "See install_nvidia_container_toolkit.md for details."
    exit 1
else
    echo "Docker GPU access verified."
fi

# Ensure HF Cache directory exists locally
mkdir -p ~/.cache/huggingface

# 5. Resolve relative model path to absolute and set up Docker volume mounts
DOCKER_VOLUME_MOUNTS=()
DOCKER_VOLUME_MOUNTS+=("-v" "$HOME/.cache/huggingface:/root/.cache/huggingface")

RESOLVED_MODEL_PATH="$QWEN_MODEL_PATH"
IS_LOCAL_MODEL=false

if [[ "$QWEN_MODEL_PATH" != /* && "$QWEN_MODEL_PATH" != [a-zA-Z]:* ]]; then
    if [ -d "$ROOT_DIR/$QWEN_MODEL_PATH" ]; then
        RESOLVED_MODEL_PATH="$ROOT_DIR/$QWEN_MODEL_PATH"
        IS_LOCAL_MODEL=true
    fi
elif [ -d "$QWEN_MODEL_PATH" ]; then
    IS_LOCAL_MODEL=true
fi

if [ "$IS_LOCAL_MODEL" = true ]; then
    echo "Local model directory detected: $RESOLVED_MODEL_PATH"
    echo "Mounting local path to /model inside the container."
    DOCKER_VOLUME_MOUNTS+=("-v" "$RESOLVED_MODEL_PATH:/model")
    CONTAINER_MODEL_PATH="/model"
else
    CONTAINER_MODEL_PATH="$QWEN_MODEL_PATH"
fi

echo "Starting vLLM Docker Container with configuration:"
echo "--------------------------------------------------------"
echo "Model Path (Host):       $QWEN_MODEL_PATH"
if [ "$IS_LOCAL_MODEL" = true ]; then
echo "Model Path (Container):  $CONTAINER_MODEL_PATH (mounted from $RESOLVED_MODEL_PATH)"
fi
echo "Served Model Name:       $QWEN_SERVED_MODEL_NAME"
echo "Host & Port (exposing):  $QWEN_HOST:$QWEN_PORT"
echo "Max Model Len:           $QWEN_MAX_MODEL_LEN"
echo "GPU Memory Util:         $QWEN_GPU_MEMORY_UTILIZATION"
echo "Max Num Sequences:       $QWEN_MAX_NUM_SEQS"
echo "Dtype:                   $QWEN_DTYPE"
echo "--------------------------------------------------------"

# Note: --runtime nvidia is included below. If this causes compatibility issues on newer Docker configurations
# where CDI/native integration is preferred, you can safely remove the '--runtime nvidia' flag and keep only '--gpus all'.

docker run --rm \
  --runtime nvidia \
  --gpus all \
  "${DOCKER_VOLUME_MOUNTS[@]}" \
  -p ${QWEN_PORT}:${QWEN_PORT} \
  --ipc=host \
  -e VLLM_API_KEY="$QWEN_API_KEY" \
  vllm/vllm-openai:latest \
  --model "$CONTAINER_MODEL_PATH" \
  --served-model-name "$QWEN_SERVED_MODEL_NAME" \
  --host "$QWEN_HOST" \
  --port "$QWEN_PORT" \
  --max-model-len "$QWEN_MAX_MODEL_LEN" \
  --gpu-memory-utilization "$QWEN_GPU_MEMORY_UTILIZATION" \
  --max-num-seqs "$QWEN_MAX_NUM_SEQS" \
  --dtype "$QWEN_DTYPE"
