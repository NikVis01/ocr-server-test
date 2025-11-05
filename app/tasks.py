from typing import List, Dict, Any
from .inference import run_paddle_ocr_vl

def process_image(image_input: str) -> List[Dict[str, Any]]:
    return run_paddle_ocr_vl(image_input)

