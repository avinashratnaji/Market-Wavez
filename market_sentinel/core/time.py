"""Timezone helpers for market-facing timestamps."""

from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo


IST = ZoneInfo("Asia/Kolkata")


def now_ist() -> datetime:
    """Return a timezone-aware timestamp in Indian Standard Time."""
    return datetime.now(IST)


def as_ist(value: datetime) -> datetime:
    """Normalize provider timestamps before displaying or persisting them."""
    if value.tzinfo is None:
        return value.replace(tzinfo=IST)
    return value.astimezone(IST)
