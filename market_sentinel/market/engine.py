"""
market/engine.py

Indian Market Engine.

Author : Market Sentinel
"""

from __future__ import annotations

from market_sentinel.market.models import (
    IndianMarketSnapshot,
)

from market_sentinel.providers.angelone.indices import (
    IndianIndicesProvider,
)


class IndianMarketEngine:

    def __init__(self):

        self.indices = IndianIndicesProvider()

    def build(self) -> IndianMarketSnapshot:

        snapshot = IndianMarketSnapshot()

        snapshot.indices = self.indices.fetch()

        return snapshot