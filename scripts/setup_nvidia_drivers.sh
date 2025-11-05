#!/usr/bin/env bash
set -euo pipefail

sudo apt-get update
sudo apt-get install -y curl docker.io nvidia-container-toolkit
sudo systemctl enable --now docker
sudo nvidia-ctk runtime configure --runtime=docker || true
sudo systemctl restart docker
echo "Verify with: nvidia-smi and docker run --rm --gpus all nvidia/cuda:12.6.0-base-ubuntu22.04 nvidia-smi"

