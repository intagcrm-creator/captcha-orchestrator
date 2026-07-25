"""Capsolver API client with task submission, polling, and balance checking."""

import asyncio
import httpx
import time
import structlog
from config import settings

logger = structlog.get_logger()


class CapsolverClient:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30)
        self.base_url = "https://api.capsolver.com"

    async def close(self):
        await self.client.aclose()

    async def submit_task(
        self,
        captcha_type: str,
        website_url: str,
        website_key: str,
        proxy: str | None = None,
        user_agent: str | None = None,
        enterprise: bool = False,
    ) -> str:
        task: dict = {
            "type": f"{captcha_type}Task",
            "websiteURL": website_url,
            "websiteKey": website_key,
        }
        if proxy:
            task["proxy"] = proxy
        if user_agent:
            task["userAgent"] = user_agent
        if enterprise:
            task["enterprise"] = True

        payload = {
            "clientKey": settings.capsolver_api_key,
            "task": task,
        }
        resp = await self.client.post(f"{self.base_url}/createTask", json=payload)
        resp.raise_for_status()
        data = resp.json()
        if data.get("errorId") != 0:
            raise RuntimeError(f"Capsolver submit error: {data}")
        return data["taskId"]

    async def get_result(self, task_id: str) -> dict:
        resp = await self.client.get(
            f"{self.base_url}/getTaskResult",
            params={"clientKey": settings.capsolver_api_key, "taskId": task_id},
        )
        resp.raise_for_status()
        return resp.json()

    async def get_balance(self) -> float:
        """Check Capsolver account balance in USD."""
        resp = await self.client.get(
            f"{self.base_url}/getBalance",
            params={"clientKey": settings.capsolver_api_key},
        )
        resp.raise_for_status()
        data = resp.json()
        if data.get("errorId") != 0:
            raise RuntimeError(f"Capsolver balance error: {data}")
        return data.get("balance", 0.0)

    async def solve(
        self,
        captcha_type: str,
        website_url: str,
        website_key: str,
        proxy: str | None = None,
        user_agent: str | None = None,
        enterprise: bool = False,
    ) -> dict | None:
        """Submit a captcha task and poll until solved or failed."""
        task_id = await self.submit_task(
            captcha_type, website_url, website_key, proxy, user_agent, enterprise
        )
        logger.info("capsolver_task_created", task_id=task_id)

        start = time.time()
        while time.time() - start < settings.max_poll_time:
            await asyncio.sleep(settings.poll_interval)
            result = await self.get_result(task_id)
            state = result.get("status")

            if state == "ready":
                solution = result.get("solution", {})
                logger.info(
                    "capsolver_solved",
                    task_id=task_id,
                    solve_time_s=round(time.time() - start, 2),
                )
                return solution

            if state == "failed" or result.get("errorId", 0) != 0:
                error_desc = result.get("errorDescription", "unknown error")
                logger.error(
                    "capsolver_failed",
                    task_id=task_id,
                    error=error_desc,
                    status=state,
                )
                return None

        logger.warning("capsolver_timeout", task_id=task_id, elapsed_s=round(time.time() - start, 2))
        return None