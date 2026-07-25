import asyncio
import structlog
from config import settings
from orchestrator import Orchestrator

structlog.configure(processors=[structlog.dev.ConsoleRenderer()])

async def main():
    orch = Orchestrator()
    await orch.start()

if __name__ == "__main__":
    asyncio.run(main())