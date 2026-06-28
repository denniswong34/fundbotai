"""FundPort Application Configuration"""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "FundBot AI"
    APP_VERSION: str = "0.1.0"

    # Database
    DATABASE_URL: str = "mysql+aiomysql://fundport:fundport_2024@localhost:3309/fundport"

    # JWT
    JWT_SECRET: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # CORS
    CORS_ORIGINS: str = "http://localhost:8081,http://localhost:5173"

    # Encryption
    ENCRYPTION_KEY: str = "change-me-in-production"

    # Broker configs
    WEBULL_APP_KEY: str = ""
    WEBULL_APP_SECRET: str = ""

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


_settings: Settings | None = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
