import logging
import os
import time

import requests
from fastapi import FastAPI, HTTPException, Request

from .queue import enqueue_job, enqueue_job_payload, get_job, start_worker

app = FastAPI(title="PaddleOCR-VL Service")

_log = logging.getLogger("paddleocr_vl.api")


def _probe_vllm_async():
    import threading

    def _run():
        base = os.getenv("VL_SERVER_URL", "http://127.0.0.1:8118/v1").rstrip("/")
        models_url = f"{base}/models"
        health_base = base.rsplit("/", 1)[0] if base.endswith(("/v1", "/vl")) else base
        health_url = f"{health_base}/health"
        for i in range(3):
            try:
                s_models = requests.get(models_url, timeout=3).status_code
                s_health = requests.get(health_url, timeout=3).status_code
                _log.info(
                    f"vllm probes models_status={s_models} health_status={s_health} base={base}"
                )
                break
            except Exception as e:
                _log.warning(f"vllm probe attempt={i+1} error={e}")
                time.sleep(1 * (i + 1))

    threading.Thread(target=_run, daemon=True).start()


@app.middleware("http")
async def _log_http(request: Request, call_next):
    t0 = time.perf_counter()
    resp = await call_next(request)
    elapsed_ms = int((time.perf_counter() - t0) * 1000)
    _log.info(f"http {request.method} {request.url.path} {resp.status_code} {elapsed_ms}ms")
    return resp


@app.on_event("startup")
async def startup_event():
    # quick non-blocking probes to the model server
    _probe_vllm_async()
    start_worker()


@app.get("/health")
def health():
    return {"status": "probably fine lol"}


@app.post("/infer")
async def infer(request: Request, body: dict):
    # New contract: model_id, input{}, execution_id, callback_url, callback_token
    if isinstance(body.get("input"), dict):
        input_obj = body["input"]
        execution_id = body.get("execution_id") or request.headers.get("X-Execution-Id")
        callback_url = body.get("callback_url")
        callback_token = body.get("callback_token") or request.headers.get("X-Callback-Token")
        model_id = body.get("model_id")
        idem_key = body.get("idempotency_key")
        if not execution_id or not callback_url:
            raise HTTPException(
                status_code=400,
                detail="Provide execution_id and callback_url",
            )
        payload = {
            "model_id": model_id,
            "input": input_obj,
            "execution_id": execution_id,
            "callback_url": callback_url,
            **({"callback_token": callback_token} if callback_token else {}),
        }
        job_id = enqueue_job_payload(payload, idem_key)
        _log.info(
            "job queued",
            extra={
                "job_id": job_id,
                "has_input": bool(input_obj),
                "callback": True,
            },
        )
        return {"job_id": job_id, "status": "queued"}
    # Back-compat contract
    url = body.get("url") or body.get("image_url") or body.get("pdf_url")
    callback_url = body.get("callback_url")
    idem_key = body.get("idempotency_key")
    if not url:
        raise HTTPException(status_code=400, detail="Provide url (pdf_url or image_url)")
    job_id = enqueue_job(url, callback_url, idem_key)
    _log.info("job queued", extra={"job_id": job_id, "url": url, "callback": bool(callback_url)})
    return {"job_id": job_id, "status": "queued"}


@app.get("/jobs/{job_id}")
def job_status(job_id: str):
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return {"job_id": job_id, "status": job.get("status")}


@app.get("/jobs/{job_id}/result")
def job_result(job_id: str):
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    status = job.get("status")
    if status == "finished":
        return {"job_id": job_id, "status": status, "result": job.get("result")}
    if status == "failed":
        raise HTTPException(status_code=500, detail=str(job.get("error")))
    return {"job_id": job_id, "status": status}
