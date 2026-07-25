import aiohttp
import time
import asyncio
import structlog
from config import settings

logger = structlog.get_logger()

class CapsolverClient:
    def __init__(self):
        self._client: aiohttp.ClientSession | None = None
        self.base_url = "https://api.capsolver.com"

    async def _get_client(self) -> aiohttp.ClientSession:
        if self._client is None or self._client.closed:
            self._client = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30)
            )
        return self._client

    async def submit_task(self, captcha_type: str, website_url: str, website_key: str, proxy: str) -> str:
        client = await self._get_client()
        task_payload = {
            "clientKey": settings.capsolver_api_key,
            "task": {
                "type": f"{captcha_type}Task",
                "websiteURL": website_url,
                "websiteKey": website_key,
                "proxy": proxy
            }
        }
        async with client.post(f"{self.base_url}/createTask", json=task_payload) as resp:
            resp.raise_for_status()
            data = await resp.json()
        if data.get("errorId") != 0:
            raise RuntimeError(f"Capsolver submit error: {data}")
        return data["taskId"]

    async def get_result(self, task_id: str) -> dict:
        client = await self._get_client()
        async with client.get(
            f"{self.base_url}/getTaskResult",
            params={"clientKey": settings.capsolver_api_key, "taskId": task_id}
        ) as resp:
            resp.raise_for_status()
            return await resp.json()

    async def get_balance(self) -> dict:
        client = await self._get_client()
        async with client.get(
            f"{self.base_url}/getBalance",
            params={"clientKey": settings.capsolver_api_key}
        ) as resp:
            resp.raise_for_status()
            return await resp.json()

    async def solve(self, captcha_type: str, website_url: str, website_key: str, proxy: str) -> dict | None:
        task_id = await self.submit_task(captcha_type, website_url, website_key, proxy)
        logger.info("capsolver_task_created", task_id=task_id)

        start = time.time()
        while time.time() - start < settings.max_poll_time:
            await asyncio.sleep(settings.poll_interval)
            result = await self.get_result(task_id)
            state = result.get("status")
            if state == "ready":
                return result.get("solution", {})
            if state == "failed" or result.get("errorId", 0) != 0:
                logger.error("capsolver_failed", task_id=task_id, error=result.get("errorDescription"))
                return None

        logger.warning("capsolver_timeout", task_id=task_id)
        return None

    async def close(self):
        if self._client and not self._client.closed:
            await self._client.close()
