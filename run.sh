VL_URL=${VL_SERVER_URL:-http://host.docker.internal:8118/v1}
REDIS_URL=${REDIS_URL:-redis://host.docker.internal:6379/0}

docker network create ocr-net

# vLLM server (exposes 8118), ensure it is on the same network and named 'vllm'
docker rm -f vllm 2>/dev/null || true
docker run -d --name vllm --network ocr-net -p 8118:8118 \
  ccr-2vdh3abv-pub.cnc.bj.baidubce.com/paddlepaddle/paddleocr-genai-vllm-server:latest

docker run -d --name redis --network ocr-net redis:7-alpine

docker run --rm --gpus all --network ocr-net \
  -e VL_SERVER_URL="http://vllm:8118/v1" \
  -e REDIS_URL="redis://redis:6379/0" \
  -p 80:8080 paddleocr-vl-service:latest
