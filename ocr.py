# ocr_service.py
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from paddleocr import PaddleOCR
import numpy as np
import cv2

app = FastAPI(title="OCR Service")

# initialize PaddleOCR once
ocr_model = PaddleOCR(lang="en", use_angle_cls=True)  # adjust params as needed

@app.post("/ocr/")
async def ocr_endpoint(file: UploadFile = File(...)):
    try:
        # read file bytes
        contents = await file.read()
        # convert bytes to numpy array
        arr = np.frombuffer(contents, dtype=np.uint8)
        img = cv2.imdecode(arr, flags=cv2.IMREAD_COLOR)
        if img is None:
            raise ValueError("Could not decode image")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid image upload: {str(e)}")

    # run OCR
    result = ocr_model.ocr(img, cls=True)
    # parse output
    output = []
    for entry in result:
        bbox = entry[0]
        text, confidence = entry[1]
        output.append({
            "text": text,
            "confidence": float(confidence),
            "bbox": [list(point) for point in bbox]
        })

    return JSONResponse(content={"results": output})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

