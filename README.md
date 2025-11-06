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

2) Start vLLM (separate container; requires CUDA >= 12.6)
```bash
docker run -it --rm --gpus all --network host \
  ccr-2vdh3abv-pub.cnc.bj.baidubce.com/paddlepaddle/paddleocr-genai-vllm-server:latest \
  paddleocr genai_server --model_name PaddleOCR-VL-0.9B --host 0.0.0.0 --port 8118 --backend vllm
```

3) Run wrapper (GCP: map host 80 -> container 8080)
```bash
./run.sh
```

4) Health check
```bash
curl -s http://<server-ip>/health
```

5) Inference (PDF URL)
```bash
curl -s -X POST http://<server-ip>/infer \
  -H 'Content-Type: application/json' \
  -d '{"pdf_url":"https://example.com/sample.pdf"}' | jq .
```

### Initialization and Packaging Notes
- Image base: `ccr-2vdh3abv-pub.cnc.bj.baidubce.com/paddlepaddle/paddleocr-vl:latest` (includes PaddleOCR‑VL and CUDA runtime).
- During build we install Paddle GPU wheel (CUDA 12.6) inside the image:
  - `paddlepaddle-gpu==3.2.1` from `https://www.paddlepaddle.org.cn/packages/stable/cu126/`
- Model source is set to BOS by default: `PADDLE_PDX_MODEL_SOURCE=BOS` (faster, reliable mirrors).
- A warm‑up step downloads required models at build time so first request is fast.
- Build prints versions, e.g.:
  - `paddle 3.2.1` (expected)
  - `paddlex <version>`
  - A `ccache` warning is harmless; we are not compiling extensions.

### Environment Variables
- `VL_SERVER_URL` (wrapper → vLLM URL). Default: `http://127.0.0.1:8118/v1`. `run.sh` maps this to `http://host.docker.internal:8118/v1` for host vLLM.
- `PADDLE_PDX_MODEL_SOURCE` (optional) set to `BOS` in the Dockerfile.

### Validation (sanity)
1) Host GPU and toolkit
```bash
nvidia-smi
docker run --rm --gpus all nvidia/cuda:12.4.0-base-ubuntu22.04 nvidia-smi
```
2) After build, check versions appeared in the build logs. At runtime:
```bash
docker exec -it <container> python -c 'import paddle;print(paddle.__version__)'
```
3) Health and sample request (see Quickstart).

### Troubleshooting
- Health ok, but jobs fail with `ModuleNotFoundError: paddle`: rebuild the image (no‑cache) so Paddle 3.2.1 GPU wheel is present.
- `Segmentation fault` on init: ensure CUDA >= 12.6 on host; use the GPU wheel above; run container with `--gpus all --shm-size=2g --ipc=host` if OOM.
- Wrapper cannot reach vLLM: confirm vLLM is running (see logs) and `VL_SERVER_URL` is reachable from the container. `run.sh` uses `host.docker.internal:8118`.

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

How to get drivers:
https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html