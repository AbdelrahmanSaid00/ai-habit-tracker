from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings (BaseSettings):
    PROJECT_NAME : str = "AI Habit Tracker Bot"
    ENVIRONMENT : str = "development"
    DATABASE_URL: str
    GEMINI_API_KEY: str
    TELEGRAM_BOT_TOKEN: str

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()