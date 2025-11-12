import logging
import os
import time
from typing import Any

from paddleocr import PaddleOCRVL

from .utils import download_to_tmp

_log = logging.getLogger("paddleocr_vl.infer")


def run_paddle_ocr_vl_url(url: str) -> dict[str, Any]:
    t0 = time.perf_counter()
    _log.info("download input", extra={"url": url})
    local_path = download_to_tmp(url)
    # Use vLLM backend for VL recognition
    vl_url = os.getenv("VL_SERVER_URL", "http://127.0.0.1:8118/v1")
    pipeline = PaddleOCRVL(vl_rec_backend="vllm-server", vl_rec_server_url=vl_url)
    _log.info(f"pipeline init (vllm backend) vl_server={vl_url}")
    output = pipeline.predict(input=local_path)
    _log.info(
        f"predict done elapsed_s={round(time.perf_counter() - t0, 3)} pages={len(output or [])}"
    )

    markdown_list = []
    markdown_images = []
    for res in output or []:
        md = getattr(res, "markdown", {})
        markdown_list.append(md)
        markdown_images.append(md.get("markdown_images", {}))

    markdown_texts = pipeline.concatenate_markdown_pages(markdown_list)
    # log a short preview to help debugging without spamming logs
    md_chars = len(markdown_texts)
    md_preview = (markdown_texts or "")[:64]
    _log.info(f"markdown built chars={md_chars} preview={md_preview!r}")

    images = {}
    for item in markdown_images:
        if not item:
            continue
        for path, image in item.items():
            # Return images as base64 PNG to keep API single-response
            import base64
            import io

            buf = io.BytesIO()
            image.save(buf, format="PNG")
            images[path] = base64.b64encode(buf.getvalue()).decode()
    _log.info(f"images encoded count={len(images)}")
    return {"markdown": markdown_texts, "images": images}


def run_paddle_ocr_vl_pdf(pdf_url: str) -> dict[str, Any]:
    # Backward-compatible alias for PDF inputs
    return run_paddle_ocr_vl_url(pdf_url)
