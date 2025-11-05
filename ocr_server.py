from fastapi import FastAPI, File, UploadFile, HTTPException, Form, Body
from fastapi.responses import JSONResponse
import numpy as np
import cv2
import requests
from paddleocr import PaddleOCRVL
import base64
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ocr-server")

app = FastAPI(title="PaddleOCR-VL Service")

@app.get("/health")
def health():
    return {"status": "ok"}

pipeline = PaddleOCRVL()

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
    # Keep BGR; log shape
    try:
        logger.info("Decoded image shape: %s", None if img is None else tuple(img.shape))
    except Exception:
        pass

    # inference
    try:
        output = pipeline.predict(img)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Inference failed: {e}")

    # format results
    results = []
    # Log raw output preview
    try:
        logger.info("Raw output count: %d", 0 if output is None else len(output))
        logger.info("Raw output preview: %s", output if output is None else output[:3])
    except Exception:
        pass

    # Each item is a result object; extract common fields robustly
    for res in (output or []):
        try:
            text = getattr(res, "text", None)
            confidence = getattr(res, "confidence", None)
            bbox = getattr(res, "bbox", None)

            # Extra logging via optional helper
            try:
                if hasattr(res, "print"):
                    logger.info("Result.print():")
                    res.print()
            except Exception:
                pass

            try:
                logger.info("Result snapshot: text=%s, conf=%s, bbox=%s", text, confidence, bbox)
            except Exception:
                pass

            results.append({
                "text": text,
                "confidence": confidence,
                "bbox": bbox
            })
        except Exception:
            continue

    return JSONResponse(content={"results": results})


