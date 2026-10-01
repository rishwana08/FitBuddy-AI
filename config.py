from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    app_name: str = "FitBuddy – AI Fitness Plan Generator"

    debug: bool = True

    database_url: str = (
        f"sqlite:///{(BASE_DIR / 'fitbuddy.db').as_posix()}"
    )

    gemini_api_key: str | None = None

    # These are configurable through .env
    workout_model: str = "gemini-2.5-flash"
    tip_model: str = "gemini-2.5-flash"

    # Allows the application to work without an API key.
    demo_mode: bool = True

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )


settings = Settings()