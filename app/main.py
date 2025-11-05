from fastapi import FastAPI, HTTPException
from .queue import queue, background_worker
from .inference import run_paddle_ocr_vl

app = FastAPI(title="PaddleOCR-VL Service")

@app.on_event("startup")
async def startup_event():
    background_worker.start()

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
    job = queue.enqueue(run_paddle_ocr_vl, image_data)
    return {"job_id": job.id, "status": "queued"}


