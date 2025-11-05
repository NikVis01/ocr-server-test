import os
from fastapi_queue import FastAPIQueue
from dotenv import load_dotenv

load_dotenv()

# Should use Redis in prod but this keeps it in memory for now.
# Redis lives in memory so if you think about it its the same thing lol.
_url = os.getenv("FASTAPI_QUEUE_URL", "memory://") 
queue = FastAPIQueue(backend=_url)
background_worker = queue.worker()

