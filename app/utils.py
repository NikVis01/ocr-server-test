import os
import tempfile

import requests


def download_pdf_to_tmp(url: str) -> str:
    return download_to_tmp(url, prefer_suffix=".pdf")


def download_to_tmp(url: str, prefer_suffix: str | None = None) -> str:
    resp = requests.get(url, timeout=60)
    resp.raise_for_status()
    # infer suffix from URL or Content-Type
    lower = url.lower()
    suffix = None
    for ext in (".pdf", ".png", ".jpg", ".jpeg"):
        if lower.endswith(ext):
            suffix = ext if ext != ".jpeg" else ".jpg"
            break
    if not suffix:
        ctype = (resp.headers.get("Content-Type") or "").lower()
        if "application/pdf" in ctype:
            suffix = ".pdf"
        elif "image/png" in ctype:
            suffix = ".png"
        elif "image/jpeg" in ctype or "image/jpg" in ctype:
            suffix = ".jpg"
    if not suffix:
        suffix = prefer_suffix or ".bin"
    fd, path = tempfile.mkstemp(suffix=suffix)
    with os.fdopen(fd, "wb") as f:
        f.write(resp.content)
    return path
