Lyceum OCR Server (PaddleOCR)

Run a minimal FastAPI server that performs OCR via PaddleOCR-VL.

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
docker run --rm -p 8080:8080 lyceum-ocr:latest
# If host has NVIDIA runtime and you want GPU: add --gpus all
# docker run --rm --gpus all -p 8080:8080 lyceum-ocr:latest
```

3) Health check
```bash
curl -s http://localhost:8080/health
```

4) Inference
- Upload a local image file:
```bash
curl -s -X POST http://localhost:8080/infer/ \
  -F "file=@/path/to/image.jpg" | jq .
```

- Use a publicly reachable image URL:
```bash
curl -s -X POST http://localhost:8080/infer/ \
  -F "url=https://example.com/image.jpg" | jq .
```

- Send base64 (JSON):
```bash
BASE64=$(base64 -w0 /path/to/image.jpg)
curl -s -H 'Content-Type: application/json' \
  -d "{\"b64\":\"$BASE64\"}" \
  http://localhost:8080/infer/ | jq .
```

### Local (no Docker)
```bash
python -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -r requirements.txt
uvicorn ocr_server:app --host 0.0.0.0 --port 8080
```

### Python client (file or base64)
```python
import base64, requests

BASE = "http://localhost:8080"

# file upload
with open("/path/to/image.jpg", "rb") as f:
    r = requests.post(f"{BASE}/infer/", files={"file": ("image.jpg", f, "image/jpeg")})
print(r.json())

# base64
with open("/path/to/image.jpg", "rb") as f:
    b64 = base64.b64encode(f.read()).decode()
r = requests.post(f"{BASE}/infer/", json={"b64": b64})
print(r.json())
```

### Endpoints
- `GET /health` → `{ "status": "ok" }`
- `POST /infer/` → JSON OCR results
  - form-data: `file` (image upload) OR `url` (image URL)

### Notes
- The server initializes the PaddleOCR pipeline at startup; first request may be slower due to model load.
- If you need GPU acceleration, use a GPU Paddle base image and ensure NVIDIA drivers and runtime are configured, then run with `--gpus all`.
