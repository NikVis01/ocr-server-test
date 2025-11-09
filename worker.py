import asyncio
import os
import signal
import sys
from typing import Any

import aioredis
import requests
from fastapi_queue import QueueWorker
from loguru import logger


# Business logic: PDF inference using our existing module
def sync_infer(redis, mysql, *, pdf_url: str, callback_url: str | None = None) -> dict[str, Any]:
    from app.inference import run_paddle_ocr_vl_pdf

    result = run_paddle_ocr_vl_pdf(pdf_url)
    if callback_url:
        try:
            requests.post(callback_url, json={"status": "finished", "result": result}, timeout=15)
        except Exception as e:
            logger.warning(f"callback failed: {e}")
    return result


route_table = {
    "/infer": sync_infer,
}

route_table_maximum_concurrency = {
    "/infer": 64,
}

queueworker = None


async def main(pid, logger):
    global queueworker
    first_time_run = True
    while True:
        run_startup, first_time_run = (True if pid != 0 else False) and first_time_run, False
        redis = aioredis.Redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0"))
        try:
            worker = QueueWorker(
                redis,
                threads=4,
                route_table_maximum_concurrency=route_table_maximum_concurrency,
                allowed_type_limit=None,
                run_startup=run_startup,
                logger=logger,
            )
            queueworker = worker
            [worker.method_register(name, func) for name, func in route_table.items()]
            await worker.run_serve()
            if worker.closeing():
                break
        except Exception as e:
            raise e
    await redis.close()
    logger.info(f"Pid: {worker.pid}, shutdown")


def sigint_capture(sig, frame):
    if queueworker:
        queueworker.graceful_shutdown(sig, frame)
    else:
        sys.exit(1)


if __name__ == "__main__":
    logger.remove()
    logger.add(sys.stderr, level="DEBUG", enqueue=True)
    signal.signal(signal.SIGINT, sigint_capture)
    for _ in range(3):
        pid = os.fork()
        if pid == 0:
            break
    asyncio.run(main(pid, logger))
