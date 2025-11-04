from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.responses import JSONResponse
import numpy as np
import cv2
import requests
from paddleocr import PaddleOCRVL

app = FastAPI(title="PaddleOCR-VL Service")

@app.get("/health")
def health():
    return {"status": "ok"}

pipeline = PaddleOCRVL()

@app.post("/infer/")
async def infer(
    file: UploadFile = File(None),
    url: str = Form(None)
):
    if not file and not url:
        raise HTTPException(status_code=400, detail="Either file upload or url must be provided")

    # get image bytes
    if file:
        contents = await file.read()
    else:
        try:
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()
            contents = resp.content
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to download image from url: {e}")

    # decode image
    arr = np.frombuffer(contents, dtype=np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if img is None:
        raise HTTPException(status_code=400, detail="Could not decode image bytes")
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    # inference
    try:
        output = pipeline.predict(img)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Inference failed: {e}")

    # format results
    results = []
    for res in output:
        results.append({
            "text": getattr(res, "text", None),
            "confidence": getattr(res, "confidence", None),
            "bbox": getattr(res, "bbox", None)
        })

    return JSONResponse(content={"results": results})


