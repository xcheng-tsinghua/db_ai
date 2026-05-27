# Install NVIDIA Container Toolkit Guide

To run vLLM inside a Docker container (`start_qwen_vllm_docker.sh`), Docker must have access to the host's GPU. This requires installing the **NVIDIA Container Toolkit** on Ubuntu 22.04 or 24.04.

---

## Step 1: Install or Verify NVIDIA Drivers

Ensure your host machine has a compatible NVIDIA driver installed:

```bash
nvidia-smi
```

If the command is missing or prints an error, install the drivers.
On Ubuntu:
```bash
sudo apt update
sudo apt install -y nvidia-driver-535 # Or another stable driver version
```
Reboot your machine after installation:
```bash
sudo reboot
```

---

## Step 2: Install Docker Engine

If Docker is not yet installed on your system:

```bash
# Add Docker's official GPG key:
sudo apt-get update
sudo apt-get install ca-certificates curl gnupg
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

# Add the repository to Apt sources:
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update

# Install Docker packages:
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```

Verify Docker is running:
```bash
sudo systemctl status docker
```

---

## Step 3: Install NVIDIA Container Toolkit

The NVIDIA Container Toolkit allows users to build and run GPU-accelerated containers.

### 1. Configure the repository
```bash
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg \
  && curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
    sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
    sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list
```

### 2. Install the package
```bash
sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit
```

### 3. Configure Docker to use NVIDIA runtime
```bash
sudo nvidia-ctk runtime configure --runtime=docker
```

### 4. Restart the Docker daemon
```bash
sudo systemctl restart docker
```

---

## Step 4: Verify Docker GPU Access

Run a test CUDA container to verify that Docker can access and use the GPU:

```bash
docker run --rm --gpus all nvidia/cuda:12.0.0-base-ubuntu22.04 nvidia-smi
```

### Successful Output
If configured correctly, the command above should print the identical `nvidia-smi` GPU table that you see on your host machine.

If this test fails, vLLM Docker-based serving will **not** work. Double-check your NVIDIA driver installation and ensure you restarted Docker.
