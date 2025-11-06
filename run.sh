#!/usr/bin/env bash
set -euo pipefail

docker run --rm --gpus all -p 80:8080 paddleocr-vl-service:latest