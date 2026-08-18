"""
briefs/morning.py

Morning Brief Builder.

Author : Market Sentinel
"""

from __future__ import annotations

from datetime import datetime
import re

from loguru import logger

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
from market_sentinel.research.options.service import DailyOptionsRadarService


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
        self.options_radar = DailyOptionsRadarService()

    def build(self) -> MorningBrief:

        brief = MorningBrief(

            generated_at=datetime.now(),

            health_score=0,

            market_sentiment="Unknown",

            confidence=0,

            top_news=[],

            indices=self._safe("Indian indices", self.indices.fetch, []),

            sectors=self._safe("sector heatmap", self.sectors.fetch, []),

            gainers=self._safe("NSE gainers", lambda: self.nse_movers.fetch("gainers"), []) or self._safe("Angel gainers", self.gainers.fetch, []),

            losers=self._safe("NSE losers", lambda: self.nse_movers.fetch("losers"), []) or self._safe("Angel losers", self.losers.fetch, []),
        )

        # ----------------------------------------------------
        # News
        # ----------------------------------------------------

        ranked_indian = self._unique_articles(self._safe(
            "Indian market news",
            lambda: self.news_ranker.rank(self.news.collect(), limit=10),
            [],
        ))
        brief.indian_news = ranked_indian[:5]
        brief.indian_events = ranked_indian[5:10]

        # Backwards compatibility for existing consumers that read top_news.
        brief.top_news = brief.indian_news

        ranked_global = self._unique_articles(self._safe("US/global market news", lambda: self.global_news.collect(limit=10), []))
        brief.global_impact_news = ranked_global[:5]
        brief.us_events = ranked_global[5:10]
        brief.crypto_news = self._unique_articles(self._safe("crypto market news", lambda: self.crypto_news.collect(limit=5), []))[:5]
        (
            brief.global_indices,
            brief.indian_adrs,
            brief.commodities,
            brief.crypto,
        ) = self._safe("external market quotes", self.external_markets.fetch, ([], [], [], []))
        brief.us_gainers = self._safe("US gainers", lambda: self.us_movers.fetch("gainers"), [])
        brief.us_losers = self._safe("US losers", lambda: self.us_movers.fetch("losers"), [])

        brief.investor_flows = self._safe("FII/DII flows", self.institutional_flows.fetch, None)

        brief.top_ipos = self._safe("IPO GMP", lambda: self.ipo_gmp.fetch_top(limit=10), [])
        brief.fo_ban_symbols = self._safe("F&O ban list", self.premarket.fetch_fo_ban, [])
        brief.fo_ban_available = self.premarket.fo_ban_available
        brief.gift_nifty = self._safe("GIFT Nifty", self.premarket.fetch_gift_nifty, None)

        (
            brief.option_research,
            brief.option_research_failures,
        ) = self._safe("10 AM F&O research", self.options_radar.run, ([], []))

        if not any(item.name.upper() == "SENSEX" for item in brief.indices):
            sensex = self._safe("Sensex", self.sensex.fetch, None)
            if sensex:
                brief.indices.insert(1, sensex)

        # Health must be calculated before the AI receives its evidence.
        # Otherwise the narrative is built from the initial 0/Unknown values.
        brief = self._safe("market-health calculation", lambda: self.health.calculate(brief), brief)
        brief.ai_summary, brief.ai_summary_source = self.summary_generator.generate(brief)
        return brief

    @staticmethod
    def _safe(label: str, operation, default):
        """A temporary provider failure must not cancel the entire brief."""
        try:
            return operation()
        except Exception as exc:
            logger.warning("{} unavailable in this run: {}", label, exc)
            return default

    @staticmethod
    def _unique_articles(articles):
        """Remove cross-feed duplicates before Telegram formatting or AI input."""
        unique = []
        seen: set[str] = set()
        for article in articles:
            title = re.sub(r"[^a-z0-9]+", " ", (article.title or "").lower()).strip()
            key = title or (article.url or "").strip().lower()
            if not key or key in seen:
                continue
            seen.add(key)
            unique.append(article)
        return unique
