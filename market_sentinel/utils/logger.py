from pathlib import Path
import sys

from loguru import logger

from market_sentinel.config import settings


LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

logger.remove()

# Windows PowerShell can inherit a legacy cp1252 console even though Telegram
# output and log files are UTF-8. Market messages legitimately contain ₹ and
# emoji, so configure the console once instead of raising after a successful
# provider call merely because a diagnostic line contains those characters.
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, OSError):
    pass

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
