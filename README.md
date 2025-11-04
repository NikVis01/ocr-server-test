Lyceum OCR Server (PaddleOCR-VL)

Run a minimal FastAPI server that performs OCR via PaddleOCR-VL.

### Requirements
- Docker (recommended) — `setup.sh` installs Docker on Ubuntu
- Optional: NVIDIA GPU + drivers + nvidia-container-runtime for GPU images

### Quickstart (Docker)
1) Build
```bash
./build.sh
```

2) Run
```bash
docker run --rm -p 8000:8000 lyceum-ocr:latest
# For GPU (if supported by your environment): add --gpus all
# docker run --rm --gpus all -p 8000:8000 lyceum-ocr:latest
```

3) Health check
```bash
curl -s http://localhost:8000/health
```

4) Inference
- Upload a local image file:
```bash
curl -s -X POST http://localhost:8000/infer/ \
  -F "file=@/path/to/image.jpg" | jq .
```

- Use a publicly reachable image URL:
```bash
curl -s -X POST http://localhost:8000/infer/ \
  -F "url=https://example.com/image.jpg" | jq .
```

### Local (no Docker)
```bash
python -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -r requirements.txt
uvicorn ocr_server:app --host 0.0.0.0 --port 8000
```

### Endpoints
- `GET /health` → `{ "status": "ok" }`
- `POST /infer/` → JSON OCR results
  - form-data: `file` (image upload) OR `url` (image URL)

### Notes
- The server imports and initializes the PaddleOCR-VL pipeline at startup; first request may be slower due to model load.
- If you need GPU acceleration in Docker, ensure your host has compatible NVIDIA drivers and the container runtime configured, then run with `--gpus all`.
