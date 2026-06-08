from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "sqlite:///./data/cs_quant.db"
    cors_origins: str = "http://localhost:5173"
    market_provider: str = "mock"
    steam_orderbook_enabled: bool = False
    steam_orderbook_item_nameids: str = "{}"
    steam_request_timeout_seconds: float = 8
    collect_item_limit: int = 0
    worker_sleep_seconds: int = 60
    push_channel: str = "none"
    wechat_webhook_url: str = ""
    qq_webhook_url: str = ""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
