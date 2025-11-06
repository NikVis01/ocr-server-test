PaddleOCR-VL Service

FastAPI service for PaddleOCR-VL. Accepts a PDF URL; exposes 8080 (mapped to host 80 on GCP); GPU REQUIRED.

### Requirements
- Docker (recommended) — `setup.sh` installs Docker on Ubuntu
- Optional: NVIDIA GPU + drivers + nvidia-container-runtime (use a GPU Paddle base if needed)

### Quickstart (Docker)
1) Build
```bash
./build.sh
```

2) Run (GCP: map host 80 -> container 8080)
```bash
./run.sh
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
