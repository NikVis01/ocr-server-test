# Default to host vLLM (requires vLLM container started with --network host)
VL_URL=${VL_SERVER_URL:-http://host.docker.internal:8118/v1}
REDIS_PASSWORD=${REDIS_PASSWORD:-demo123}

docker run -d --name redis -p 6379:6379 redis:7-alpine

docker run -it --rm --gpus all --network host \
  ccr-2vdh3abv-pub.cnc.bj.baidubce.com/paddlepaddle/paddleocr-genai-vllm-server:latest \
  paddleocr genai_server --model_name PaddleOCR-VL-0.9B --host 0.0.0.0 --port 8118 --backend vllm

docker run --rm --gpus all \
  --add-host=host.docker.internal:host-gateway \
  -e VL_SERVER_URL="$VL_URL" \
  -e REDIS_PASSWORD="$REDIS_PASSWORD" \
  -p 80:8080 paddleocr-vl-service:latest