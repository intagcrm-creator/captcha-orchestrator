import httpx
import structlog
from config import settings

logger = structlog.get_logger()

class ProxyManager:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=10)
        self.pool: list[str] = []
        self._index = 0

    async def refresh_pool(self):
        resp = await self.client.get(
            settings.gsocks_proxy_url,
            params={"country": settings.gsocks_country},
            headers={"Authorization": f"Bearer {settings.gsocks_api_key}"}
        )
        resp.raise_for_status()
        data = resp.json()
        # GSOCKS typically returns [{"ip":"...","port":...}, ...]
        self.pool = [f"{p['ip']}:{p['port']}" for p in data]
        self._index = 0
        logger.info("proxy_pool_refreshed", count=len(self.pool))

    async def get_proxy(self) -> str | None:
        if not self.pool:
            await self.refresh_pool()
        if not self.pool:
            return None
        proxy = self.pool[self._index % len(self.pool)]
        self._index += 1
        return proxy