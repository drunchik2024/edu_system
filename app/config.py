from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Переменные читаются из .env; переменные окружения имеют приоритет над файлом
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    DATABASE_URL: str = "postgresql+asyncpg://postgres:password@localhost:5432/edu_system"
    SECRET_KEY: str = "change-me-in-production-must-be-32-chars-min"
    # 480 мин = 8 часов — токен живёт один рабочий день
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480
    ALGORITHM: str = "HS256"


settings = Settings()
