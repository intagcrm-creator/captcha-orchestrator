from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Solver keys
    capsolver_api_key: str
    two_captcha_api_key: str = ""

    # Proxy
    gsocks_api_key: str = ""
    gsocks_proxy_url: str = "socks5://58Br8eN7r_s_LCHxL5rT:aykNYnxfSWJi@residential.gsocks.net:10000"
    gsocks_country: str = "us"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Worker settings
    worker_concurrency: int = 5
    max_retries: int = 3
    poll_interval: float = 2.0
    max_poll_time: float = 60.0

    # API server
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # Logging
    log_level: str = "INFO"


settings = Settings()
