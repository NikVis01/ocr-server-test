import json
import logging
import os
import threading
import time
from typing import Any
from uuid import uuid4

import requests
from redis import Redis

_log = logging.getLogger("paddleocr_vl.queue")

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
redis: Redis = Redis.from_url(REDIS_URL)
_queue_key = os.getenv("QUEUE_KEY", "ocr_jobs")


def _job_key(job_id: str) -> str:
    return f"job:{job_id}"


def _save_job(job_id: str, **fields: Any) -> None:
    redis.hset(
        _job_key(job_id),
        mapping={k: json.dumps(v) if not isinstance(v, str) else v for k, v in fields.items()},
    )


def _load_job(job_id: str) -> dict[str, Any] | None:
    data = redis.hgetall(_job_key(job_id))
    if not data:
        return None
    out: dict[str, Any] = {}
    for k, v in data.items():
        ks = k.decode()
        try:
            out[ks] = json.loads(v)
        except Exception:
            out[ks] = v.decode()
    return out


def _idempotent_callback(callback_url: str, job_id: str, payload: dict[str, Any]) -> None:
    # best-effort idempotency across instances using Redis
    cb_key = f"idemp:cb:{job_id}:{hash(callback_url)}"
    if not redis.setnx(cb_key, "1"):
        return
    redis.expire(cb_key, 86400)
    try:
        _log.info("callback send", extra={"job_id": job_id, "url": callback_url})
        resp = requests.post(callback_url, json=payload, timeout=15)
        if 200 <= resp.status_code < 300:
            _log.info("callback ok", extra={"job_id": job_id, "status_code": resp.status_code})
        else:
            # include small slice of body for debugging
            body = (resp.text or "")[:512]
            _log.warning(
                "callback non-2xx",
                extra={"job_id": job_id, "status_code": resp.status_code, "body": body},
            )
    except Exception as e:
        _log.warning(
            "callback failed", extra={"job_id": job_id, "error": str(e), "url": callback_url}
        )


def _process(payload: dict[str, Any]):
    from .inference import run_paddle_ocr_vl_pdf

    job_id = payload["job_id"]
    pdf_url = payload["pdf_url"]
    callback_url = payload.get("callback_url")
    _save_job(job_id, status="running", started_at=time.time())
    try:
        result = run_paddle_ocr_vl_pdf(pdf_url)
        # concise summary for observability
        summary_chars = len(result.get("markdown") or "")
        summary_images = len(result.get("images") or {})
        preview = (result.get("markdown") or "")[:128]
        msg = (
            f"model ok job={job_id} chars={summary_chars} " f"img={summary_images} prev={preview!r}"
        )
        _log.info(msg)
        _save_job(job_id, status="finished", result=result, finished_at=time.time())
        if callback_url:
            _idempotent_callback(
                callback_url, job_id, {"job_id": job_id, "status": "finished", "result": result}
            )
    except Exception as e:
        _save_job(job_id, status="failed", error=str(e), finished_at=time.time())
        if callback_url:
            _idempotent_callback(
                callback_url, job_id, {"job_id": job_id, "status": "failed", "error": str(e)}
            )


def enqueue_job(pdf_url: str, callback_url: str | None, idem_key: str | None) -> str:
    job_id = idem_key or str(uuid4())
    if _load_job(job_id):
        return job_id
    _save_job(job_id, status="queued")
    payload = json.dumps({"job_id": job_id, "pdf_url": pdf_url, "callback_url": callback_url})
    redis.rpush(_queue_key, payload)
    return job_id


def get_job(job_id: str) -> dict[str, Any] | None:
    return _load_job(job_id)


def start_worker():
    def _worker_loop():
        _log.info("redis worker started", extra={"queue": _queue_key})
        while True:
            try:
                item = redis.blpop(_queue_key, timeout=5)
                if not item:
                    continue
                _, raw = item
                payload = json.loads(raw)
                _process(payload)
            except Exception as e:
                _log.exception("worker error", extra={"error": str(e)})

    t = threading.Thread(target=_worker_loop, daemon=True)
    t.start()
