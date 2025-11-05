from typing import List, Dict, Any
import numpy as np
from paddleocr import PaddleOCRVL
from .utils import load_image

_pipeline = PaddleOCRVL()

def run_paddle_ocr_vl(image_input: str) -> List[Dict[str, Any]]:
    img = load_image(image_input)
    output = _pipeline.predict(img)
    results = []
    for res in (output or []):
        results.append({
            "text": getattr(res, "text", None),
            "confidence": getattr(res, "confidence", None),
            "bbox": getattr(res, "bbox", None)
        })
    return results

