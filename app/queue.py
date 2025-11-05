import os
from dotenv import load_dotenv
from redis import Redis
from rq import Queue

load_dotenv()

REDIS_URL = os.getenv("REDIS_URL") or os.getenv("FASTAPI_QUEUE_URL") or "redis://localhost:6379/0"

def _redis_from_url(url: str) -> Redis:
    # Simple parser that lets Redis() handle most defaults
    return Redis.from_url(url)

redis_conn: Redis = _redis_from_url(REDIS_URL)
queue: Queue = Queue("ocr_tasks", connection=redis_conn)

def enqueue(func, *args, **kwargs):
    return queue.enqueue(func, *args, **kwargs)

