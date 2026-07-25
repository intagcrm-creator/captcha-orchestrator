"""Pydantic models for task validation and serialization."""

from pydantic import BaseModel, Field, HttpUrl
from typing import Optional
from enum import Enum


class CaptchaType(str, Enum):
    RECAPTCHA_V2 = "ReCaptchaV2"
    RECAPTCHA_V3 = "ReCaptchaV3"
    HCAPTCHA = "HCaptcha"
    TURNSTILE = "Turnstile"
    FUNCAPTCHA = "FunCaptcha"


class CaptchaTask(BaseModel):
    """A captcha solving task."""
    id: str = Field(..., description="Unique task identifier")
    type: CaptchaType = Field(default=CaptchaType.RECAPTCHA_V2, description="Captcha type")
    website_url: HttpUrl = Field(..., description="URL of the website with captcha")
    website_key: str = Field(..., description="Captcha widget key/ID")
    session_id: Optional[str] = Field(None, description="Session ID for consistent proxy assignment")
    proxy: Optional[str] = Field(None, description="Specific proxy to use (optional)")
    callback_url: Optional[str] = Field(None, description="Webhook URL to receive results")


class TaskResult(BaseModel):
    """Result of a solved captcha task."""
    task_id: str
    result: dict
    solved_at: str
    solve_time_ms: float
    proxy_used: str
    captcha_type: str


class MetricsResponse(BaseModel):
    """Metrics for the orchestrator."""
    solved: int
    failed: int
    retried: int
    worker_count: int
    proxy_pool_size: int
    uptime_seconds: float