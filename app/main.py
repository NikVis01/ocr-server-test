from fastapi import FastAPI, HTTPException, BackgroundTasks
from .queue import enqueue, get_job
from .inference import run_paddle_ocr_vl_pdf

app = FastAPI(title="PaddleOCR-VL Service")

@app.on_event("startup")
async def startup_event():
    pass

@app.get("/health")
def health():
    return {"status": "probably fine lol"}

@app.post("/infer")
async def infer(request: dict, background_tasks: BackgroundTasks):
    pdf_url = request.get("pdf_url")
    if not pdf_url:
        raise HTTPException(status_code=400, detail="Provide pdf_url")
    job_id = enqueue(background_tasks, run_paddle_ocr_vl_pdf, pdf_url)
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


