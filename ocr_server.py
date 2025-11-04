from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.responses import JSONResponse
import numpy as np
import cv2
import requests
from paddleocr import PaddleOCR

app = FastAPI(title="PaddleOCR Service")

@app.get("/health")
def health():
    return {"status": "ok"}

pipeline = PaddleOCR(use_angle_cls=True, lang='en')

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
    # PaddleOCR expects BGR; keep as-is

    # inference
    try:
        output = pipeline.ocr(img, cls=True)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Inference failed: {e}")

    # format results
    results = []
    # output is list per image; each item is list of (bbox, (text, score))
    for lines in output:
        if not lines:
            continue
        for item in lines:
            bbox = item[0]
            text = item[1][0]
            score = float(item[1][1])
            results.append({
                "text": text,
                "confidence": score,
                "bbox": bbox
            })

    return JSONResponse(content={"results": results})


