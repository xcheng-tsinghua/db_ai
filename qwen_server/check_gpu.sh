#!/usr/bin/env bash

# GPU and Host system status check script

echo "========================================================="
echo "       System & GPU Compatibility Check for vLLM         "
echo "========================================================="

# 1. Check NVIDIA Driver & GPU presence
echo -e "\n[1/5] Checking GPU presence and drivers (nvidia-smi)..."
if command -v nvidia-smi &> /dev/null; then
    echo "SUCCESS: nvidia-smi is available."
    nvidia-smi --query-gpu=name,driver_version,memory.total,power.draw --format=csv
else
    echo "ERROR: nvidia-smi is NOT found. Please verify that NVIDIA drivers are installed."
    echo "vLLM requires a physical NVIDIA GPU and CUDA support."
fi

# 2. Check System Memory
echo -e "\n[2/5] Checking system memory (RAM)..."
if command -v free &> /dev/null; then
    free -h
    TOTAL_RAM=$(free -g | awk '/^Mem:/{print $2}')
    if [ "$TOTAL_RAM" -lt 16 ]; then
        echo "WARNING: Your system has less than 16GB of RAM. vLLM loading Qwen-14B may experience issues."
    else
        echo "SUCCESS: System has ${TOTAL_RAM}GB of RAM."
    fi
else
    echo "Warning: 'free' command not available. Skipping memory size verification."
fi

# 3. Check Disk Space
echo -e "\n[3/5] Checking disk space for model files..."
FREE_SPACE=$(df -BG ~ | awk 'NR==2 {print $4}' | sed 's/G//')
if [ -n "$FREE_SPACE" ]; then
    echo "Free space in home directory: ${FREE_SPACE} GB."
    if [ "$FREE_SPACE" -lt 25 ]; then
        echo "WARNING: Less than 25GB free space available. Downloading models might fail."
    else
        echo "SUCCESS: Sufficient disk space detected."
    fi
else
    echo "Warning: Unable to check disk space. Ensure at least 20GB is free."
fi

# 4. Check Docker installation
echo -e "\n[4/5] Checking Docker daemon status..."
if command -v docker &> /dev/null; then
    if docker info &> /dev/null; then
        echo "SUCCESS: Docker is installed and running."
    else
        echo "ERROR: Docker daemon is not running. Please start Docker."
    fi
else
    echo "WARNING: Docker is not installed or not in PATH. Only local vLLM serving can be used."
fi

# 5. Check Docker GPU runtime compatibility
echo -e "\n[5/5] Checking Docker GPU container access..."
if command -v docker &> /dev/null && docker info &> /dev/null; then
    echo "Running CUDA diagnostic container (nvidia/cuda:12.0.0-base-ubuntu22.04)..."
    if docker run --rm --gpus all nvidia/cuda:12.0.0-base-ubuntu22.04 nvidia-smi &> /dev/null; then
        echo "SUCCESS: Docker GPU access is configured correctly (NVIDIA Container Toolkit is active)."
    else
        echo "ERROR: Docker cannot access GPUs. Docker runs will fail."
        echo "Please install NVIDIA Container Toolkit. See 'install_nvidia_container_toolkit.md' for guides."
    fi
else
    echo "SKIPPED: Docker is not running or not available."
fi

echo -e "\n========================================================="
echo "Check complete. Review warnings/errors before deploying."
echo "========================================================="
