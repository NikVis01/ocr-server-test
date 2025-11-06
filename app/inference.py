from typing import Dict, Any
import logging
import time
from paddleocr import PaddleOCRVL
from .utils import download_pdf_to_tmp
import paddle

_log = logging.getLogger("paddleocr_vl.infer")

# Enforce GPU usage (fail fast if not available)
try:
    paddle.set_device("gpu")
except Exception as e:
    raise RuntimeError(f"GPU device required but not available: {e}")

def run_paddle_ocr_vl_pdf(pdf_url: str) -> Dict[str, Any]:
    t0 = time.perf_counter()
    _log.info("download pdf", extra={"pdf_url": pdf_url})
    local_pdf = download_pdf_to_tmp(pdf_url)
    # Prefer GPU if available
    pipeline = PaddleOCRVL()
    _log.info("pipeline init (native backend)")
    output = pipeline.predict(input=local_pdf)
    _log.info("predict done", extra={"elapsed_s": round(time.perf_counter()-t0, 3), "pages": len(output or [])})

    markdown_list = []
    markdown_images = []
    for res in (output or []):
        md = getattr(res, "markdown", {})
        markdown_list.append(md)
        markdown_images.append(md.get("markdown_images", {}))

    markdown_texts = pipeline.concatenate_markdown_pages(markdown_list)
    _log.info("markdown built", extra={"markdown_chars": len(markdown_texts)})

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
    _log.info("images encoded", extra={"count": len(images)})
    return {"markdown": markdown_texts, "images": images}

