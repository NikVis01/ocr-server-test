from typing import Dict, Any
import os
from paddleocr import PaddleOCRVL
from .utils import download_pdf_to_tmp

_vl_server = os.getenv("VL_SERVER_URL", "http://127.0.0.1:8118/v1")
_use_gpu = os.getenv("USE_GPU", "true").lower() in ("1", "true", "yes")

def run_paddle_ocr_vl_pdf(pdf_url: str) -> Dict[str, Any]:
    local_pdf = download_pdf_to_tmp(pdf_url)
    # Prefer GPU if available
    if _use_gpu:
        try:
            import paddle
            paddle.set_device("gpu")
        except Exception:
            pass
    pipeline = PaddleOCRVL(vl_rec_backend="vllm-server", vl_rec_server_url=_vl_server)
    output = pipeline.predict(input=local_pdf)

    markdown_list = []
    markdown_images = []
    for res in (output or []):
        md = getattr(res, "markdown", {})
        markdown_list.append(md)
        markdown_images.append(md.get("markdown_images", {}))

    markdown_texts = pipeline.concatenate_markdown_pages(markdown_list)

    images = {}
    for idx, item in enumerate(markdown_images):
        if not item:
            continue
        for path, image in item.items():
            # Return images as base64 PNG to keep API single-response
            import io, base64
            buf = io.BytesIO()
            image.save(buf, format="PNG")
            images[path] = base64.b64encode(buf.getvalue()).decode()

    return {"markdown": markdown_texts, "images": images}

