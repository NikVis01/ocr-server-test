from typing import Dict, Any
import os
import logging
import time
from paddleocr import PaddleOCRVL
from .utils import download_pdf_to_tmp

_vl_server = os.getenv("VL_SERVER_URL", "http://127.0.0.1:8118/v1")
_use_gpu = os.getenv("USE_GPU", "true").lower() in ("1", "true", "yes")
_log = logging.getLogger("paddleocr_vl.infer")

def run_paddle_ocr_vl_pdf(pdf_url: str) -> Dict[str, Any]:
    t0 = time.perf_counter()
    _log.info("download pdf", extra={"pdf_url": pdf_url})
    local_pdf = download_pdf_to_tmp(pdf_url)
    # Prefer GPU if available
    if _use_gpu:
        try:
            import paddle
            paddle.set_device("gpu")
            _log.info("device set", extra={"device": "gpu"})
        except Exception as e:
            _log.warning("gpu not available, continuing", extra={"error": str(e)})
    pipeline = PaddleOCRVL(vl_rec_backend="vllm-server", vl_rec_server_url=_vl_server)
    _log.info("pipeline init", extra={"vl_server": _vl_server})
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

