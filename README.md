PaddleOCR-VL Service

FastAPI service for PaddleOCR-VL. Accepts a PDF URL; exposes 8080; GPU-ready. Uses FastAPI BackgroundTasks for lightweight in-process queuing with job polling endpoints. The service configures PaddleOCR-VL to use a vLLM server for VL recognition per `how-to-do-it.md`.

### Requirements
- Docker (recommended) — `setup.sh` installs Docker on Ubuntu
- Optional: NVIDIA GPU + drivers + nvidia-container-runtime (use a GPU Paddle base if needed)

### Quickstart (Docker)
1) Build (GPU wheel)
```bash
./build.sh
```

2) Run (GCP: map host 80 -> container 8080)
```bash
./run.sh
# Equivalent:
# docker run --rm --gpus all \
#   --add-host=host.docker.internal:host-gateway \
#   -e USE_GPU=true \
#   -e VL_SERVER_URL=http://host.docker.internal:8118/v1 \
#   -p 80:8080 paddleocr-vl-service:latest
```

3) Health check
```bash
curl -s http://<server-ip>/health
```

4) Inference (PDF URL)
```bash
curl -s -X POST http://<server-ip>/infer \
  -H 'Content-Type: application/json' \
  -d '{"pdf_url":"https://example.com/sample.pdf"}' | jq .
```

Then poll the job status and result:
```bash
curl -s http://<server-ip>/jobs/<job_id>
curl -s http://<server-ip>/jobs/<job_id>/result | jq .
```

### Local (no Docker)
```bash
python -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8080
```

### Python client (PDF URL)
```python
import requests

BASE = "http://localhost:8080"

# submit pdf url
r = requests.post(f"{BASE}/infer", json={"pdf_url": "https://example.com/sample.pdf"})
job = r.json()["job_id"]
print(job)
print(requests.get(f"{BASE}/jobs/{job}/result").json())
```

### Endpoints
- `GET /health` → `{ "status": "ok" }`
- `POST /infer` → body `{ pdf_url }`; returns `{ job_id, status }`
- `GET /jobs/{job_id}` → `{ job_id, status }`
- `GET /jobs/{job_id}/result` → `{ job_id, status, result }` when finished (result contains `markdown` and base64 `images`)

### Notes
- The server initializes the PaddleOCR pipeline at startup; first request may be slower due to model load.
- If you need GPU acceleration, use a GPU Paddle base image and ensure NVIDIA drivers and runtime are configured, then run with `--gpus all`.
