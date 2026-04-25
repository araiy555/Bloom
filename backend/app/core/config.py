from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    DATABASE_URL: str = "sqlite:///./bloom.db"
    SECRET_KEY: str = "change-me"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7
    JWT_ALGORITHM: str = "HS256"

    UPLOAD_DIR: str = "./uploads"

    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""

    DEFAULT_PROVIDER: str = "openai"
    DEFAULT_OPENAI_MODEL: str = "gpt-4o-mini"
    DEFAULT_ANTHROPIC_MODEL: str = "claude-haiku-4-5-20251001"

    CORS_ORIGINS: str = "http://localhost:3000"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
