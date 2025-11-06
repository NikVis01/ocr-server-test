#!/usr/bin/env bash
set -euo pipefail

# If vLLM runs on the same VM, use host-gateway so the container can reach it
VLLM_URL=${VL_SERVER_URL:-http://host.docker.internal:8118/v1}

docker run --rm --gpus all \
  --add-host=host.docker.internal:host-gateway \
  -e USE_GPU=true \
  -e VL_SERVER_URL="$VLLM_URL" \
  -p 80:8080 paddleocr-vl-service:latest