"""
market/models.py

Market Snapshot models.

Author : Market Sentinel
Version : 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass, field

from market_sentinel.providers.angelone.models import (
    IndexSnapshot,
)


@dataclass(slots=True)
class IndianMarketSnapshot:
    """
    Complete Indian Market Snapshot.
    """

    indices: list[IndexSnapshot] = field(default_factory=list)

    sectors: list[IndexSnapshot] = field(default_factory=list)

    gainers: list = field(default_factory=list)

    losers: list = field(default_factory=list)