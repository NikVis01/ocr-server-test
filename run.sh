#!/usr/bin/env bash
set -euo pipefail

# Default to host vLLM (requires vLLM container started with --network host)
VL_URL=${VL_SERVER_URL:-http://host.docker.internal:8118/v1}

docker run --rm --gpus all \
  --add-host=host.docker.internal:host-gateway \
  -e VL_SERVER_URL="$VL_URL" \
  -p 80:8080 paddleocr-vl-service:latest