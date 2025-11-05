PaddleOCR-VL Service

FastAPI + fastapi-queue service for PaddleOCR-VL. Accepts base64 or URL; exposes 8080; GPU-ready.

### Requirements
- Docker (recommended) — `setup.sh` installs Docker on Ubuntu
- Optional: NVIDIA GPU + drivers + nvidia-container-runtime (use a GPU Paddle base if needed)

### Quickstart (Docker)
1) Build
```bash
./build.sh
```

2) Run
```bash
docker run --rm -p 80:80 paddleocr-vl-service:latest
# If host has NVIDIA runtime and you want GPU: add --gpus all
# docker run --rm --gpus all -p 80:80 paddleocr-vl-service:latest
```

3) Health check
```bash
curl -s http://localhost:80/health
```

4) Inference
- URL (JSON):
```bash
curl -s -X POST http://localhost:80/infer \
  -H 'Content-Type: application/json' \
  -d '{"image_url":"https://example.com/image.jpg"}' | jq .
```

- Base64 (JSON):
```bash
BASE64=$(base64 -w0 /path/to/image.jpg)
curl -s -X POST http://localhost:80/infer \
  -H 'Content-Type: application/json' \
  -d "{\"image_base64\":\"$BASE64\"}" | jq .
```

### Local (no Docker)
```bash
python -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 80
```

### Python client (URL or base64)
```python
import base64, requests

BASE = "http://localhost:80"

# url
r = requests.post(f"{BASE}/infer", json={"image_url": "https://example.com/image.jpg"})
print(r.json())

# base64
with open("/path/to/image.jpg", "rb") as f:
    b64 = base64.b64encode(f.read()).decode()
r = requests.post(f"{BASE}/infer", json={"image_base64": b64})
print(r.json())
```

### Endpoints
- `GET /health` → `{ "status": "ok" }`
- `POST /infer` → returns `{ job_id, status }`; queue configured via `FASTAPI_QUEUE_URL`

### Notes
- The server initializes the PaddleOCR pipeline at startup; first request may be slower due to model load.
- If you need GPU acceleration, use a GPU Paddle base image and ensure NVIDIA drivers and runtime are configured, then run with `--gpus all`.
