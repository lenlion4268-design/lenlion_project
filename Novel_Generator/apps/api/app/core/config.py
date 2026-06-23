from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "local"
    api_prefix: str = "/api"
    database_url: str = (
        "postgresql+psycopg://novel:novel_password@localhost:5432/novel_generator"
    )
    cors_origins: str = "http://localhost:3000"


settings = Settings()
