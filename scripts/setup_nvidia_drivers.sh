#!/usr/bin/env bash
set -euo pipefail

# NVIDIA Container Toolkit install (Ubuntu) — official guide:
# https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html

sudo apt-get update
sudo apt-get install -y --no-install-recommends curl gnupg2 ca-certificates docker.io
sudo systemctl enable --now docker

# Add repo (signed-by) — use stable/deb to avoid 404s on unknown releases
sudo mkdir -p /usr/share/keyrings
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | \
  sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list >/dev/null <<'EOF'
deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://nvidia.github.io/libnvidia-container/stable/deb/ /
EOF

sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit

# Configure Docker runtime
if command -v nvidia-ctk >/dev/null 2>&1; then
  sudo nvidia-ctk runtime configure --runtime=docker
else
  # Fallback daemon.json
  sudo mkdir -p /etc/docker
  sudo tee /etc/docker/daemon.json >/dev/null <<'JSON'
{
  "runtimes": {
    "nvidia": { "path": "nvidia-container-runtime", "runtimeArgs": [] }
  }
}
JSON
fi

sudo systemctl restart docker

echo "Verify:"
echo "  nvidia-smi"
echo "  sudo docker run --rm --gpus all nvidia/cuda:12.4.0-base-ubuntu22.04 nvidia-smi"

