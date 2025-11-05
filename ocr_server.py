from fastapi import FastAPI, File, UploadFile, HTTPException, Form, Body
from fastapi.responses import JSONResponse
import numpy as np
import cv2
import requests
from paddleocr import PaddleOCR
import base64

app = FastAPI(title="PaddleOCR Service")

@app.get("/health")
def health():
    return {"status": "ok"}

pipeline = PaddleOCR(use_angle_cls=True, lang='en')

@app.post("/infer/")
async def infer(
    file: UploadFile = File(None),
    url: str = Form(None),
    b64: str = Body(None)
):
    if not file and not url and not b64:
        raise HTTPException(status_code=400, detail="Provide one of: file, url, or JSON b64")

    # get image bytes
    if file:
        contents = await file.read()
    elif url:
        try:
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()
            contents = resp.content
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to download image from url: {e}")
    else:
        try:
            payload = b64.split(',')[-1] if b64 else ''
            contents = base64.b64decode(payload, validate=False)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid base64 payload: {e}")

    # decode image
    arr = np.frombuffer(contents, dtype=np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if img is None:
        raise HTTPException(status_code=400, detail="Could not decode image bytes")
    # PaddleOCR expects BGR; keep as-is

    # inference
    try:
        output = pipeline.ocr(img)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Inference failed: {e}")

    # format results
    results = []
    # output is list per image; each item is typically [bbox, (text, score)]
    for lines in output:
        if not lines:
            continue
        for item in lines:
            if not item or len(item) < 2:
                continue
            bbox = item[0]
            info = item[1]
            text, score = None, None
            if isinstance(info, (list, tuple)) and len(info) >= 2:
                text = info[0]
                try:
                    score = float(info[1])
                except Exception:
                    score = None
            elif isinstance(info, str):
                text = info
            results.append({
                "text": text,
                "confidence": score,
                "bbox": bbox
            })

    return JSONResponse(content={"results": results})


