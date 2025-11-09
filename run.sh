VL_URL=${VL_SERVER_URL:-http://host.docker.internal:8118/v1}
REDIS_URL=${REDIS_URL:-redis://host.docker.internal:6379/0}

docker network create ocr-net

docker run -d --name redis --network ocr-net redis:7-alpine

docker run --rm --gpus all --network ocr-net \
  -e VL_SERVER_URL="http://vllm:8118/v1" \
  -e REDIS_URL="redis://redis:6379/0" \
  -p 80:8080 paddleocr-vl-service:latest
