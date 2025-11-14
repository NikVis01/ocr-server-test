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


def _idempotent_callback(
    callback_url: str,
    job_id: str,
    payload: dict[str, Any],
    headers: dict[str, str] | None = None,
) -> None:
    # best-effort idempotency across instances using Redis
    status = payload.get("status") or "unknown"
    cb_key = f"idemp:cb:{job_id}:{status}:{hash(callback_url)}"
    if not redis.setnx(cb_key, "1"):
        return
    redis.expire(cb_key, 86400)
    try:
        _log.info("callback send", extra={"job_id": job_id, "url": callback_url, "status": status})
        hdrs = {"Content-Type": "application/json"}
        if headers:
            hdrs.update(headers)
        resp = requests.post(callback_url, json=payload, headers=hdrs, timeout=15)
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
    from .inference import run_paddle_ocr_vl_url
    from .utils import save_base64_image_to_tmp

    job_id = payload["job_id"]
    # New contract
    input_obj = payload.get("input") or {}
    execution_id = payload.get("execution_id")
    callback_token = payload.get("callback_token")
    callback_url = payload.get("callback_url")
    headers = {}
    if execution_id:
        headers["X-Execution-Id"] = str(execution_id)
    if callback_token:
        headers["X-Callback-Token"] = str(callback_token)
    # Back-compat fields
    url = payload.get("url") or payload.get("pdf_url") or payload.get("image_url")
    if not url:
        url = input_obj.get("url") or input_obj.get("pdf_url") or input_obj.get("image_url")
    image_b64 = input_obj.get("image_data")
    text_input = (input_obj.get("text") or "").strip()
    _save_job(job_id, status="running", started_at=time.time())
    try:
        # Optional progress callback
        if callback_url:
            _idempotent_callback(
                callback_url,
                job_id,
                {"job_id": job_id, "status": "in_progress"},
                headers=headers,
            )
        local_path = None
        if image_b64:
            local_path = save_base64_image_to_tmp(image_b64)
            result = run_paddle_ocr_vl_url(local_path)
        elif url:
            result = run_paddle_ocr_vl_url(url)
        elif text_input:
            raise RuntimeError("text input not supported")
        else:
            raise RuntimeError("no supported input provided")
        # shape final result to contract
        model_name = payload.get("model_id") or "paddle-ocr-vl"
        pages = [{"page": 1, "text": result.get("markdown") or "", "blocks": []}]
        final_result = {
            "model_id": model_name,
            **({"input_url": url} if url else {}),
            "pages": pages,
            "markdown": result.get("markdown") or "",
            "usage": {"total_tokens": 0},
        }
        # concise summary for observability
        summary_chars = len(result.get("markdown") or "")
        summary_images = len(result.get("images") or {})
        preview = (result.get("markdown") or "")[:128]
        msg = (
            f"model ok job={job_id} chars={summary_chars} " f"img={summary_images} prev={preview!r}"
        )
        _log.info(msg)
        _save_job(job_id, status="finished", result=final_result, finished_at=time.time())
        if callback_url:
            _idempotent_callback(
                callback_url,
                job_id,
                {"job_id": job_id, "status": "finished", "result": final_result},
                headers=headers,
            )
    except Exception as e:
        _save_job(job_id, status="failed", error=str(e), finished_at=time.time())
        if callback_url:
            _idempotent_callback(
                callback_url,
                job_id,
                {"job_id": job_id, "status": "failed", "error": str(e)},
                headers=headers,
            )


def enqueue_job(url: str, callback_url: str | None, idem_key: str | None) -> str:
    job_id = idem_key or str(uuid4())
    if _load_job(job_id):
        return job_id
    _save_job(job_id, status="queued")
    payload = json.dumps({"job_id": job_id, "url": url, "callback_url": callback_url})
    redis.rpush(_queue_key, payload)
    return job_id


def enqueue_job_payload(job_payload: dict[str, Any], idem_key: str | None) -> str:
    job_id = idem_key or str(uuid4())
    if _load_job(job_id):
        return job_id
    job_payload = dict(job_payload)
    job_payload["job_id"] = job_id
    _save_job(job_id, status="queued")
    redis.rpush(_queue_key, json.dumps(job_payload))
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
