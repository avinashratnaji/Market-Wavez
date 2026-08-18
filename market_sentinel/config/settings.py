"""
Application configuration.

Loads all environment variables from the .env file and exposes
them through a single Settings object.
"""

from dataclasses import dataclass
from pathlib import Path
import os

from dotenv import load_dotenv


# Project Root
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Load .env
load_dotenv(PROJECT_ROOT / ".env")


@dataclass(frozen=True)
class Settings:
    """Application settings."""

    # ------------------------------------------------------------------
    # Project
    # ------------------------------------------------------------------
    PROJECT_NAME: str = "Market Sentinel"
    VERSION: str = "0.1.0"

    # ------------------------------------------------------------------
    # PostgreSQL
    # ------------------------------------------------------------------
    POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", "localhost")
    POSTGRES_PORT: int = int(os.getenv("POSTGRES_PORT", 5432))
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "market_sentinel")
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "")

    # ------------------------------------------------------------------
    # Telegram
    # ------------------------------------------------------------------
    TELEGRAM_ENABLED: bool = (
            os.getenv("TELEGRAM_ENABLED", "false").lower() == "true"
    )

    # TELEGRAM_TOKEN was used in the project's original .env template.
    # Prefer the explicit name but remain compatible with existing installs.
    TELEGRAM_BOT_TOKEN: str = (
        os.getenv("TELEGRAM_BOT_TOKEN", "")
        or os.getenv("TELEGRAM_TOKEN", "")
    )

    TELEGRAM_CHAT_ID: str = os.getenv(
        "TELEGRAM_CHAT_ID", ""
    )
    TELEGRAM_COMMAND_CHAT_ID: str = os.getenv("TELEGRAM_COMMAND_CHAT_ID", "")

    # GitHub Actions dispatch for on-demand Telegram commands. Use a fine-
    # grained token with Actions: write for this repository only.
    GITHUB_REPOSITORY: str = os.getenv("GITHUB_REPOSITORY", "")
    GITHUB_ACTIONS_TOKEN: str = os.getenv("GITHUB_ACTIONS_TOKEN", "")
    GITHUB_REF: str = os.getenv("GITHUB_REF", "main")

    # ------------------------------------------------------------------
    # OpenAI market-summary generation
    # ------------------------------------------------------------------
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-5.6")

    # ------------------------------------------------------------------
    # Angel One
    # ------------------------------------------------------------------
    ANGEL_API_KEY: str = os.getenv("ANGEL_API_KEY", "")
    ANGEL_CLIENT_ID: str = os.getenv("ANGEL_CLIENT_ID", "")
    ANGEL_PIN: str = os.getenv("ANGEL_PIN", "")
    ANGEL_TOTP_SECRET: str = os.getenv("ANGEL_TOTP_SECRET", "")

    # ------------------------------------------------------------------
    # Logging
    # ------------------------------------------------------------------
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    #-------------------------------------------------------------------
    # Scheduler
    # -------------------------------------------------------------------
    COLLECT_INTERVAL: int = int(
        os.getenv("COLLECT_INTERVAL", "300")
    )

    RUN_ON_STARTUP: bool = (
            os.getenv("RUN_ON_STARTUP", "true").lower() == "true"
    )

    @property
    def DATABASE_URL(self) -> str:
        """SQLAlchemy PostgreSQL connection string."""

        return (
            f"postgresql+psycopg2://"
            f"{self.POSTGRES_USER}:"
            f"{self.POSTGRES_PASSWORD}@"
            f"{self.POSTGRES_HOST}:"
            f"{self.POSTGRES_PORT}/"
            f"{self.POSTGRES_DB}"
        )


settings = Settings()
