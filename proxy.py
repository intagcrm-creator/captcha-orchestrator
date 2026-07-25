import aiohttp
import structlog
from config import settings

logger = structlog.get_logger()

class ProxyManager:
    def __init__(self):
        self.pool: list[str] = []
        self._index = 0
        self._client: aiohttp.ClientSession | None = None

    async def _get_client(self) -> aiohttp.ClientSession:
        if self._client is None or self._client.closed:
            self._client = aiohttp.ClientSession()
        return self._client

    async def refresh_pool(self):
        client = await self._get_client()
        try:
            async with client.get(
                "https://api.gsocks.net/v1/proxies",
                params={"country": settings.gsocks_country},
                headers={"Authorization": f"Bearer {settings.gsocks_api_key}"},
            ) as resp:
                resp.raise_for_status()
                data = await resp.json()
                self.pool = [f"{p['ip']}:{p['port']}" for p in data]
                self._index = 0
                logger.info("proxy_pool_refreshed", count=len(self.pool))
        except Exception as e:
            logger.error("proxy_pool_refresh_failed", error=str(e))

    async def get_proxy(self) -> str | None:
        if not self.pool:
            await self.refresh_pool()
        if not self.pool:
            return None
        proxy = self.pool[self._index % len(self.pool)]
        self._index += 1
        return proxy

    async def close(self):
        if self._client and not self._client.closed:
            await self._client.close()
