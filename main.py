import asyncio
import structlog
from fastapi import FastAPI
from config import settings
from orchestrator import Orchestrator

structlog.configure(processors=[structlog.dev.ConsoleRenderer()])

app = FastAPI(title="Captcha Orchestrator", version="1.0.0")

orchestrator: Orchestrator | None = None


@app.on_event("startup")
async def startup():
    global orchestrator
    orchestrator = Orchestrator()
    await orchestrator.start()


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/balance")
async def balance():
    if orchestrator and orchestrator.capsolver:
        return await orchestrator.capsolver.get_balance()
    return {"balance_usd": 0}


@app.get("/metrics")
async def metrics():
    if orchestrator:
        return orchestrator.metrics
    return {"solved": 0, "failed": 0, "retried": 0}


@app.get("/balance")
async def balance():
    if orchestrator and orchestrator.capsolver:
        return await orchestrator.capsolver.get_balance()
    return {"balance_usd": 0}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.api_host, port=settings.api_port)
