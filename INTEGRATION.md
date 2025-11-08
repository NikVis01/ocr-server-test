# Using the OCR Wrapper from your main API

This service exposes a tiny HTTP API for asynchronous PDF parsing via PaddleOCR‑VL (with vLLM backend). Your main API only needs to call the wrapper; it does not call vLLM directly.

## Endpoints
- `POST /infer` → queue a job
  - body (JSON):
    - `pdf_url` (string, required): publicly reachable PDF
    - `callback_url` (string, optional): if set, the wrapper POSTs results to this URL
    - `idempotency_key` (string, optional): stable identifier to dedupe repeated submits (optional; send a new value or omit to allow duplicates)
  - returns: `{ "job_id": "...", "status": "queued" }`

- `GET /jobs/{job_id}` → `{ job_id, status }`
  - `status` ∈ { `queued`, `running`, `finished`, `failed` }

- `GET /jobs/{job_id}/result` → when finished
  - success: `{ job_id, status: "finished", result: { markdown: string, images: { path: base64_png, ... } } }`
  - error: HTTP 500 with `{ detail: "..." }` if `status == failed`

## Recommended flow (webhook + minimal polling fallback)
1) Submit with a webhook:
```bash
curl -s -X POST http://<ocr-host>/infer \
  -H 'Content-Type: application/json' \
  --data-binary '{
    "pdf_url":"https://example.com/file.pdf",
    "callback_url":"https://main-api.internal/ocr/callback"
  }'
# => { "job_id": "...", "status": "queued" }
```
2) The wrapper POSTs to `callback_url` when done:
- success:
```json
{ "job_id": "...", "status": "finished", "result": { "markdown": "...", "images": { "p0/img1.png": "<base64>" } } }
```
- failure:
```json
{ "job_id": "...", "status": "failed", "error": "..." }
```
3) Optional: if webhooks aren’t possible, poll infrequently:
```bash
curl -s http://<ocr-host>/jobs/<job_id>
curl -s http://<ocr-host>/jobs/<job_id>/result | jq .
```

## Minimal Python client (submit + webhook handler)
```python
import time, requests

OCR = "http://ocr-wrapper.internal"  # wrapper base URL

# Submit a job
resp = requests.post(f"{OCR}/infer", json={
    "pdf_url": "https://example.com/file.pdf",
    "callback_url": "https://main-api.internal/ocr/callback"
}, timeout=30)
job_id = resp.json()["job_id"]
print("queued", job_id)

# Example callback handler (FastAPI skeleton):
# from fastapi import FastAPI, Request
# app = FastAPI()
# @app.post("/ocr/callback")
# async def ocr_callback(payload: dict):
#     job_id = payload["job_id"]
#     status = payload["status"]
#     if status == "finished":
#         markdown = payload["result"]["markdown"]
#         images = payload["result"].get("images", {})
#         # persist markdown/images; mark job done
#     else:
#         # mark failed and decide on retry policy
#     return {"ok": True}
```

## Auth & security
- Keep the wrapper on a private network; only the main API should reach it.
- For webhooks, add a shared secret or HMAC header so your main API can authenticate the sender.

## Timeouts & retries
- Submit timeout ~30s is sufficient; completion time depends on PDF size/model warm‑up.
- If the submit call fails transiently, you can retry. To dedupe, send `idempotency_key` (any stable string per document). If you want duplicates, omit it.

## Redis vs in‑memory queue
- Default: the wrapper can run without Redis (in‑memory queue; single instance only).
- For persistence and multi‑instance processing, run Redis and set `REDIS_URL` (e.g., `redis://host:6379/0`).

## vLLM backend
- The wrapper needs a running vLLM‑based PaddleOCR‑VL server (paddlex genai_server). Point the wrapper via `VL_SERVER_URL` (e.g., `http://host.docker.internal:8118/v1`).


