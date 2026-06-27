from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "local"
    api_prefix: str = "/api"
    database_url: str = (
        "postgresql+psycopg://novel:novel_password@localhost:5432/novel_generator"
    )
    cors_origins: str = "http://localhost:3000"
    ai_provider: str = "mock"
    ai_model: str = "mock-writer"
    openai_api_key: str | None = None
    openai_base_url: str = "https://api.openai.com/v1"
    ai_request_timeout_seconds: float = 120.0
    ai_batch_max_chapters: int = 5
    ai_model_outline: str | None = None
    ai_model_volume: str | None = None
    ai_model_chapter: str | None = None
    ai_model_profile_fast: str | None = None
    ai_model_profile_quality: str | None = None
    local_storage_dir: str = "./storage"
    generation_force_sync: bool = False
    redis_url: str | None = None
    generation_queue_backend: str = "auto"
    redis_queue_name: str = "novel:generation"
    celery_broker_url: str | None = None
    celery_result_backend: str | None = None
    celery_queue_name: str = "novel:generation"
    publish_platform_preset: str = "default"
    publish_webhook_url: str | None = None
    publish_webhook_secret: str | None = None
    publish_platform_api_url: str | None = None
    publish_platform_api_token: str | None = None
    style_sample_max_chars: int = 12000
    style_upload_max_mb: int = 10
    style_analysis_force_sync: bool = False


settings = Settings()
