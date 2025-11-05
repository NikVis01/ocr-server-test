from typing import Callable, Any, Dict, Optional
from uuid import uuid4
from fastapi import BackgroundTasks

# Simple in-memory job store for background tasks
_jobs: Dict[str, Dict[str, Optional[Any]]] = {}

def _run_and_store(job_id: str, func: Callable[[Any], Any], arg: Any) -> None:
    try:
        _jobs[job_id]["status"] = "running"
        result = func(arg)
        _jobs[job_id]["result"] = result
        _jobs[job_id]["status"] = "finished"
    except Exception as e:  # pragma: no cover
        _jobs[job_id]["error"] = str(e)
        _jobs[job_id]["status"] = "failed"

def enqueue(background_tasks: BackgroundTasks, func: Callable[[Any], Any], arg: Any) -> str:
    job_id = str(uuid4())
    _jobs[job_id] = {"status": "queued", "result": None, "error": None}
    background_tasks.add_task(_run_and_store, job_id, func, arg)
    return job_id

def get_job(job_id: str) -> Optional[Dict[str, Optional[Any]]]:
    return _jobs.get(job_id)

