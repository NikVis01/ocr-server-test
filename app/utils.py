import base64
import io
import requests
from PIL import Image
import numpy as np

def load_image(source: str) -> np.ndarray:
    if source.startswith("http://") or source.startswith("https://"):
        resp = requests.get(source, timeout=15)
        resp.raise_for_status()
        img = Image.open(io.BytesIO(resp.content)).convert("RGB")
        return np.array(img)
    payload = source.split(',')[-1]
    img_bytes = base64.b64decode(payload)
    img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
    return np.array(img)

