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

# 2. Set default values for Qwen2.5-7B-Instruct
QWEN_MODEL_PATH=${QWEN_MODEL_PATH:-"/data/models/Qwen2.5-7B-Instruct"}
QWEN_SERVED_MODEL_NAME=${QWEN_SERVED_MODEL_NAME:-"qwen7b"}
QWEN_HOST=${QWEN_HOST:-"127.0.0.1"}
QWEN_PORT=${QWEN_PORT:-8001}
QWEN_DEVICE=${QWEN_DEVICE:-"cuda"}
QWEN_DTYPE=${QWEN_DTYPE:-"auto"}
QWEN_MAX_NEW_TOKENS=${QWEN_MAX_NEW_TOKENS:-2048}
QWEN_TEMPERATURE=${QWEN_TEMPERATURE:-0.2}
QWEN_TOP_P=${QWEN_TOP_P:-0.8}
QWEN_REPETITION_PENALTY=${QWEN_REPETITION_PENALTY:-1.05}

# 3. Check local model path and config.json
# Resolve relative paths if configured relative to ROOT_DIR
if [[ "$QWEN_MODEL_PATH" != /* && "$QWEN_MODEL_PATH" != [a-zA-Z]:* ]]; then
    if [ -d "$ROOT_DIR/$QWEN_MODEL_PATH" ]; then
        QWEN_MODEL_PATH="$ROOT_DIR/$QWEN_MODEL_PATH"
    fi
fi

if [ ! -d "$QWEN_MODEL_PATH" ]; then
    echo "Error: Local model directory '$QWEN_MODEL_PATH' does not exist."
    exit 1
fi

if [ ! -f "$QWEN_MODEL_PATH/config.json" ]; then
    echo "Error: config.json not found in model directory '$QWEN_MODEL_PATH'."
    exit 1
fi

# 4. Print configuration details
echo "Starting Transformers Qwen API Server with configuration:"
echo "--------------------------------------------------------"
echo "Model Path:              $QWEN_MODEL_PATH"
echo "Served Model Name:       $QWEN_SERVED_MODEL_NAME"
echo "Host & Port:             $QWEN_HOST:$QWEN_PORT"
echo "Device:                  $QWEN_DEVICE"
echo "Dtype:                   $QWEN_DTYPE"
echo "Max New Tokens:          $QWEN_MAX_NEW_TOKENS"
echo "Temperature:             $QWEN_TEMPERATURE"
echo "Top P:                   $QWEN_TOP_P"
echo "Repetition Penalty:      $QWEN_REPETITION_PENALTY"
echo "--------------------------------------------------------"

# Export variables so the Python process inherits them
export QWEN_MODEL_PATH
export QWEN_SERVED_MODEL_NAME
export QWEN_HOST
export QWEN_PORT
export QWEN_DEVICE
export QWEN_DTYPE
export QWEN_MAX_NEW_TOKENS
export QWEN_TEMPERATURE
export QWEN_TOP_P
export QWEN_REPETITION_PENALTY

# Add root directory to PYTHONPATH so Python can locate the module package
export PYTHONPATH="$ROOT_DIR:$PYTHONPATH"

# 5. Start the server using uvicorn
exec uvicorn qwen_server_transformers.server:app --host "$QWEN_HOST" --port "$QWEN_PORT"
