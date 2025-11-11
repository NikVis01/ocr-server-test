import logging
import os
import time
from typing import Any

from paddleocr import PaddleOCRVL

from .utils import download_pdf_to_tmp

_log = logging.getLogger("paddleocr_vl.infer")


def run_paddle_ocr_vl_pdf(pdf_url: str) -> dict[str, Any]:
    t0 = time.perf_counter()
    _log.info("download pdf", extra={"pdf_url": pdf_url})
    local_pdf = download_pdf_to_tmp(pdf_url)
    # Use vLLM backend for VL recognition
    vl_url = os.getenv("VL_SERVER_URL", "http://127.0.0.1:8118/v1")
    pipeline = PaddleOCRVL(vl_rec_backend="vllm-server", vl_rec_server_url=vl_url)
    _log.info("pipeline init (vllm backend)", extra={"vl_server": vl_url})
    output = pipeline.predict(input=local_pdf)
    _log.info(
        "predict done",
        extra={"elapsed_s": round(time.perf_counter() - t0, 3), "pages": len(output or [])},
    )

    markdown_list = []
    markdown_images = []
    for res in output or []:
        md = getattr(res, "markdown", {})
        markdown_list.append(md)
        markdown_images.append(md.get("markdown_images", {}))

    markdown_texts = pipeline.concatenate_markdown_pages(markdown_list)
    # log a short preview to help debugging without spamming logs
    _log.info(
        "markdown built",
        extra={
            "markdown_chars": len(markdown_texts),
            "preview": (markdown_texts or "")[:256],
        },
    )

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
    _log.info("images encoded", extra={"count": len(images)})
    return {"markdown": markdown_texts, "images": images}
