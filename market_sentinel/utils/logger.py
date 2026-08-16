from pathlib import Path

from loguru import logger

from market_sentinel.config import settings


LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

logger.remove()

# Console
logger.add(
    sink=lambda msg: print(msg, end=""),
    level=settings.LOG_LEVEL,
    colorize=True,
)

# File
logger.add(
    LOG_DIR / "market_sentinel.log",
    rotation="10 MB",
    retention="30 days",
    level=settings.LOG_LEVEL,
    encoding="utf-8",
)

__all__ = ["logger"]