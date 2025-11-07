from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
import os
import redis.asyncio as aioredis
from fastapi_queue import DistributedTaskApplyManager
from .queue import enqueue_job, get_job, start_worker

app = FastAPI(title="PaddleOCR-VL Service")

REDIS_URL = os.getenv("REDIS_URL") or os.getenv("FASTAPI_QUEUE_URL") or "redis://localhost:6379/0"
redis = aioredis.from_url(REDIS_URL)

@app.on_event("startup")
async def startup_event():
    start_worker()

@app.get("/health")
def health():
    return {"status": "probably fine lol"}

@app.post("/infer")
async def infer(req: Request, body: dict):
    pdf_url = body.get("pdf_url")
    callback_url = body.get("callback_url")
    idem_key = body.get("idempotency_key")
    if not pdf_url:
        raise HTTPException(status_code=400, detail="Provide pdf_url")
    async with DistributedTaskApplyManager(redis=redis, request_path=req.url.path) as gate:
        if not gate.success():
            return JSONResponse(status_code=503, content="Service Temporarily Unavailable")
        job_id = enqueue_job(pdf_url, callback_url, idem_key)
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


