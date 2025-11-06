import os
import tempfile
import requests

def download_pdf_to_tmp(url: str) -> str:
    resp = requests.get(url, timeout=60)
    resp.raise_for_status()
    suffix = ".pdf"
    fd, path = tempfile.mkstemp(suffix=suffix)
    with os.fdopen(fd, "wb") as f:
        f.write(resp.content)
    return path

