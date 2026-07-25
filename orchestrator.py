import asyncio
import json
import structlog
import redis.asyncio as redis
from config import settings
from capsolver import CapsolverClient
from proxy import ProxyManager

logger = structlog.get_logger()

class Orchestrator:
    def __init__(self):
        self.redis = redis.from_url(settings.redis_url)
        self.capsolver = CapsolverClient()
        self.proxy_mgr = ProxyManager()
        self.metrics = {"solved": 0, "failed": 0, "retried": 0}

    async def start(self):
        await self.proxy_mgr.refresh_pool()
        logger.info("orchestrator_started", concurrency=settings.worker_concurrency)
        workers = [asyncio.create_task(self.worker(i)) for i in range(settings.worker_concurrency)]
        await asyncio.gather(*workers)

    async def worker(self, idx: int):
        logger.info("worker_started", id=idx)
        while True:
            try:
                # Blocking pop from Redis queue
                raw = await self.redis.blpop("captcha_queue", timeout=1)
                if not raw:
                    continue
                _, task_json = raw
                task = json.loads(task_json)
                await self.process(task)
            except Exception as e:
                logger.exception("worker_error", worker=idx, error=str(e))

    async def process(self, task: dict):
        task_id = task.get("id")
        captcha_type = task.get("type", "ReCaptchaV2Task")
        website_url = task.get("website_url")
        website_key = task.get("website_key")

        for attempt in range(1, settings.max_retries + 1):
            proxy = await self.proxy_mgr.get_proxy()
            if not proxy:
                logger.error("no_proxy_available", task_id=task_id)
                self.metrics["failed"] += 1
                return

            logger.info("solving_attempt", task_id=task_id, attempt=attempt, proxy=proxy)
            result = await self.capsolver.solve(captcha_type, website_url, website_key, proxy)

            if result:
                self.metrics["solved"] += 1
                # Push result to downstream queue or webhook
                await self.redis.rpush("captcha_results", json.dumps({"task_id": task_id, "result": result}))
                return
            else:
                self.metrics["retried"] += 1
                await asyncio.sleep(1 * attempt)  # backoff

        self.metrics["failed"] += 1
        logger.error("task_failed", task_id=task_id, retries_exhausted=True)