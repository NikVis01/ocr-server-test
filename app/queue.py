from typing import Any, Dict, Optional
from uuid import uuid4
import os, json, time, logging, requests
from redis import Redis
from fastapi_queue import FastAPIQueue

_log = logging.getLogger("paddleocr_vl.queue")

REDIS_URL = os.getenv("REDIS_URL") or os.getenv("FASTAPI_QUEUE_URL") or "redis://localhost:6379/0"
redis: Redis = Redis.from_url(REDIS_URL)
queue = FastAPIQueue(backend=REDIS_URL)
worker = queue.worker()

def _job_key(job_id: str) -> str:
    return f"job:{job_id}"

def _save_job(job_id: str, **fields: Any) -> None:
    redis.hset(_job_key(job_id), mapping={k: json.dumps(v) if not isinstance(v, str) else v for k, v in fields.items()})

def _load_job(job_id: str) -> Optional[Dict[str, Any]]:
    data = redis.hgetall(_job_key(job_id))
    if not data:
        return None
    out: Dict[str, Any] = {}
    for k, v in data.items():
        ks = k.decode()
        try:
            out[ks] = json.loads(v)
        except Exception:
            out[ks] = v.decode()
    return out

def _idempotent_callback(callback_url: str, job_id: str, payload: Dict[str, Any]) -> None:
    key = f"idemp:cb:{job_id}:{hash(callback_url)}"
    if not redis.setnx(key, "1"):
        return
    redis.expire(key, 86400)
    try:
        requests.post(callback_url, json=payload, timeout=15)
    except Exception as e:
        _log.warning("callback failed", extra={"job_id": job_id, "error": str(e)})

def _process(payload: Dict[str, Any]):
    from .inference import run_paddle_ocr_vl_pdf
    job_id = payload["job_id"]
    pdf_url = payload["pdf_url"]
    callback_url = payload.get("callback_url")
    _save_job(job_id, status="running", started_at=time.time())
    try:
        result = run_paddle_ocr_vl_pdf(pdf_url)
        _save_job(job_id, status="finished", result=result, finished_at=time.time())
        if callback_url:
            _idempotent_callback(callback_url, job_id, {"job_id": job_id, "status": "finished", "result": result})
    except Exception as e:
        _save_job(job_id, status="failed", error=str(e), finished_at=time.time())
        if callback_url:
            _idempotent_callback(callback_url, job_id, {"job_id": job_id, "status": "failed", "error": str(e)})

def enqueue_job(pdf_url: str, callback_url: Optional[str], idem_key: Optional[str]) -> str:
    job_id = idem_key or str(uuid4())
    if _load_job(job_id):
        return job_id
    _save_job(job_id, status="queued")
    queue.enqueue(_process, {"job_id": job_id, "pdf_url": pdf_url, "callback_url": callback_url})
    return job_id

def get_job(job_id: str) -> Optional[Dict[str, Any]]:
    return _load_job(job_id)

