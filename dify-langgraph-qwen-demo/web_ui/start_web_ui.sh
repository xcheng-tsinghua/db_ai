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

# 2. Set default AGENT_API_URL if not set
export AGENT_API_URL=${AGENT_API_URL:-"http://127.0.0.1:8000/agent/invoke"}

echo "Starting Streamlit Test Web UI on 0.0.0.0:8501"
echo "Targeting API Endpoint: $AGENT_API_URL"
echo "--------------------------------------------------------"

# 3. Start Streamlit UI
exec streamlit run "$SCRIPT_DIR/app.py" --server.address 0.0.0.0 --server.port 8501
