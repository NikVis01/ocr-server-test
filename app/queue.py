from typing import Callable, Any, Dict, Optional
from uuid import uuid4
from fastapi import BackgroundTasks
import logging
import time

# Simple in-memory job store for background tasks
_jobs: Dict[str, Dict[str, Optional[Any]]] = {}
_log = logging.getLogger("paddleocr_vl.queue")

def _run_and_store(job_id: str, func: Callable[[Any], Any], arg: Any) -> None:
    start = time.perf_counter()
    _jobs[job_id]["status"] = "running"
    _jobs[job_id]["started_at"] = start
    try:
        _log.info("job start", extra={"job_id": job_id})
        result = func(arg)
        _jobs[job_id]["result"] = result
        _jobs[job_id]["status"] = "finished"
        _jobs[job_id]["finished_at"] = time.perf_counter()
        _jobs[job_id]["duration_s"] = (_jobs[job_id]["finished_at"] or 0) - start
        _log.info("job done", extra={"job_id": job_id, "duration_s": _jobs[job_id]["duration_s"]})
    except Exception as e:  # pragma: no cover
        _jobs[job_id]["error"] = str(e)
        _jobs[job_id]["status"] = "failed"
        _jobs[job_id]["finished_at"] = time.perf_counter()
        _jobs[job_id]["duration_s"] = (_jobs[job_id]["finished_at"] or 0) - start
        _log.exception("job failed", extra={"job_id": job_id})

def enqueue(background_tasks: BackgroundTasks, func: Callable[[Any], Any], arg: Any) -> str:
    job_id = str(uuid4())
    _jobs[job_id] = {"status": "queued", "result": None, "error": None, "started_at": None, "finished_at": None, "duration_s": None}
    _log.info("job queued", extra={"job_id": job_id})
    background_tasks.add_task(_run_and_store, job_id, func, arg)
    return job_id

def get_job(job_id: str) -> Optional[Dict[str, Optional[Any]]]:
    return _jobs.get(job_id)

