from fastapi import FastAPI, HTTPException
from .queue import enqueue, queue
from .inference import run_paddle_ocr_vl
from rq.job import Job

app = FastAPI(title="PaddleOCR-VL Service")

@app.on_event("startup")
async def startup_event():
    pass

@app.get("/health")
def health():
    return {"status": "probably fine lol"}

@app.post("/infer")
async def infer(request: dict):
    img_b64 = request.get("image_base64")
    img_url = request.get("image_url")
    image_data = img_b64 or img_url
    if not image_data:
        raise HTTPException(status_code=400, detail="Provide image_base64 or image_url")
    job = enqueue(run_paddle_ocr_vl, image_data)
    return {"job_id": job.id, "status": "queued"}

@app.get("/jobs/{job_id}")
def job_status(job_id: str):
    job = Job.fetch(job_id, connection=queue.connection)
    return {"job_id": job.id, "status": job.get_status()}

@app.get("/jobs/{job_id}/result")
def job_result(job_id: str):
    job = Job.fetch(job_id, connection=queue.connection)
    if job.is_finished:
        return {"job_id": job.id, "status": job.get_status(), "result": job.result}
    if job.is_failed:
        raise HTTPException(status_code=500, detail=str(job.exc_info))
    return {"job_id": job.id, "status": job.get_status()}


