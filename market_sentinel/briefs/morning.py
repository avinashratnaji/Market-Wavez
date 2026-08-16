"""
briefs/morning.py

Morning Brief Builder.

Author : Market Sentinel
"""

from __future__ import annotations

from datetime import datetime

from market_sentinel.briefs.health import (
    MarketHealthEngine,
)

from market_sentinel.briefs.models import (
    MorningBrief,
)

from market_sentinel.providers.angelone.indices import (
    IndianIndicesProvider,
)

from market_sentinel.providers.angelone.sectors import (
    SectorProvider,
)

from market_sentinel.providers.angelone.gainers import (
    GainersProvider,
)

from market_sentinel.providers.angelone.losers import (
    LosersProvider,
)

from market_sentinel.providers.news.indian_market_news import (
    IndianMarketNews,
)

from market_sentinel.providers.news.news_ranker import (
    NewsRanker,
)

from market_sentinel.providers.news.global_impact_news import (
    GlobalImpactNews,
)
from market_sentinel.providers.news.crypto_market_news import CryptoMarketNews
from market_sentinel.providers.external_markets import ExternalMarketsProvider
from market_sentinel.providers.nse_movers import NseMoversProvider
from market_sentinel.providers.premarket import PreMarketProvider
from market_sentinel.providers.sensex import SensexProvider
from market_sentinel.providers.us_movers import UsMarketMoversProvider

from market_sentinel.providers.market_brief_data import (
    InstitutionalFlowProvider,
    IpoGmpProvider,
)

from market_sentinel.briefs.ai_summary import (
    MarketSummaryGenerator,
)


class MorningBriefBuilder:

    def __init__(self):

        self.indices = IndianIndicesProvider()

        self.sectors = SectorProvider()

        self.gainers = GainersProvider()

        self.losers = LosersProvider()

        self.health = MarketHealthEngine()

        # The briefing feed must be India-first.  The collector removes
        # irrelevant global/personal-finance stories; NewsRanker then scores,
        # clusters and diversifies the final event-level selection.
        self.news = IndianMarketNews()

        self.news_ranker = NewsRanker()

        self.global_news = GlobalImpactNews()
        self.crypto_news = CryptoMarketNews()
        self.external_markets = ExternalMarketsProvider()
        self.nse_movers = NseMoversProvider()
        self.premarket = PreMarketProvider()
        self.sensex = SensexProvider()
        self.us_movers = UsMarketMoversProvider()

        self.institutional_flows = InstitutionalFlowProvider()

        self.ipo_gmp = IpoGmpProvider()

        self.summary_generator = MarketSummaryGenerator()

    def build(self) -> MorningBrief:

        brief = MorningBrief(

            generated_at=datetime.now(),

            health_score=0,

            market_sentiment="Unknown",

            confidence=0,

            top_news=[],

            indices=self.indices.fetch(),

            sectors=self.sectors.fetch(),

            gainers=self.nse_movers.fetch("gainers") or self.gainers.fetch(),

            losers=self.nse_movers.fetch("losers") or self.losers.fetch(),
        )

        # ----------------------------------------------------
        # News
        # ----------------------------------------------------

        brief.indian_news = self.news_ranker.rank(
            self.news.collect(),
            limit=5,
        )

        # Backwards compatibility for existing consumers that read top_news.
        brief.top_news = brief.indian_news

        brief.global_impact_news = self.global_news.collect(limit=5)
        brief.crypto_news = self.crypto_news.collect(limit=5)
        (
            brief.global_indices,
            brief.indian_adrs,
            brief.commodities,
            brief.crypto,
        ) = self.external_markets.fetch()
        brief.us_gainers = self.us_movers.fetch("gainers")
        brief.us_losers = self.us_movers.fetch("losers")

        brief.investor_flows = self.institutional_flows.fetch()

        brief.top_ipos = self.ipo_gmp.fetch_top(limit=10)
        brief.fo_ban_symbols = self.premarket.fetch_fo_ban()
        brief.fo_ban_available = self.premarket.fo_ban_available
        brief.gift_nifty = self.premarket.fetch_gift_nifty()

        if not any(item.name.upper() == "SENSEX" for item in brief.indices):
            sensex = self.sensex.fetch()
            if sensex:
                brief.indices.insert(1, sensex)

        brief.ai_summary, brief.ai_summary_source = (
            self.summary_generator.generate(brief)
        )

        return self.health.calculate(
            brief,
        )
