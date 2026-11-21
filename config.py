from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings (BaseSettings):
    PROJECT_NAME : str = "AI Habit Tracker Bot"
    ENVIRONMENT : str = "development"
    DATABASE_URL: str
    GEMINI_API_KEY: str | None = None
    TELEGRAM_BOT_TOKEN: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )
    def require_bot_secrets(self) -> None:
        missing = []
        if not self.GEMINI_API_KEY:
            missing.append("GEMINI_API_KEY")
        if not self.TELEGRAM_BOT_TOKEN:
            missing.append("TELEGRAM_BOT_TOKEN")
        if missing:
            raise ValueError(f"Missing required bot secrets: {', '.join(missing)}")
settings = Settings()