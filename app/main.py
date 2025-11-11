import logging
import time

from fastapi import FastAPI, HTTPException, Request

from .queue import enqueue_job, get_job, start_worker

app = FastAPI(title="PaddleOCR-VL Service")

_log = logging.getLogger("paddleocr_vl.api")


@app.middleware("http")
async def _log_http(request: Request, call_next):
    t0 = time.perf_counter()
    resp = await call_next(request)
    _log.info(
        "http",
        extra={
            "method": request.method,
            "path": request.url.path,
            "status": resp.status_code,
            "elapsed_ms": int((time.perf_counter() - t0) * 1000),
        },
    )
    return resp


@app.on_event("startup")
async def startup_event():
    start_worker()


@app.get("/health")
def health():
    return {"status": "probably fine lol"}


@app.post("/infer")
async def infer(request: Request, body: dict):
    pdf_url = body.get("pdf_url")
    callback_url = body.get("callback_url")
    idem_key = body.get("idempotency_key")
    if not pdf_url:
        raise HTTPException(status_code=400, detail="Provide pdf_url")
    job_id = enqueue_job(pdf_url, callback_url, idem_key)
    _log.info(
        "job queued", extra={"job_id": job_id, "pdf_url": pdf_url, "callback": bool(callback_url)}
    )
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
