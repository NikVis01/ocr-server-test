#!/usr/bin/env bash
set -euo pipefail

# Build the service image with GPU Paddle wheel
docker build \
  --build-arg PADDLE_PACKAGE="paddlepaddle-gpu==2.6.1" \
  --build-arg PADDLE_INDEX="https://pypi.tuna.tsinghua.edu.cn/simple" \
  -t paddleocr-vl-service:latest .