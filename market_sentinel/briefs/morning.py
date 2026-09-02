"""
briefs/morning.py

Morning Brief Builder.

Author : Market Sentinel
"""

from __future__ import annotations

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
from market_sentinel.core.time import now_ist
from market_sentinel.providers.macro_calendar import UsMacroCalendarProvider
from market_sentinel.providers.market_leaders import MarketLeadersProvider
from market_sentinel.providers.company_names import CompanyNameProvider
from market_sentinel.providers.news.summary_enricher import NewsSummaryEnricher
from market_sentinel.providers.stock_discovery import StockDiscoveryProvider


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
        self.macro_calendar = UsMacroCalendarProvider()
        self.market_leaders = MarketLeadersProvider()
        self.company_names = CompanyNameProvider()
        self.news_summaries = NewsSummaryEnricher()
        self.stock_discovery = StockDiscoveryProvider()

    def build(self, window: str = "full") -> MorningBrief:
        """Build only the evidence used by the requested scheduled brief."""
        window = (window or "full").lower()
        if window not in {"full", "morning", "afternoon", "night"}:
            raise ValueError(f"Unknown briefing window: {window}")
        needs_india = window in {"full", "morning", "afternoon"}
        needs_morning = window in {"full", "morning"}
        needs_afternoon = window in {"full", "afternoon"}
        needs_night = window in {"full", "night"}
        needs_external = window in {"full", "morning", "night"}

        brief = MorningBrief(

            generated_at=now_ist(),

            health_score=0,

            market_sentiment="Unknown",

            confidence=0,

            top_news=[],

            indices=self._safe("Indian indices", self.indices.fetch, []) if needs_india else [],

            sectors=self._safe("sector heatmap", self.sectors.fetch, []) if needs_india else [],

            # Keep a broad internal universe.  The public brief still shows
            # only the strongest researched names, but a 40-name input can
            # miss a high-volume catalyst that is not the day's biggest move.
            gainers=(self._safe("NSE gainers", lambda: self.nse_movers.fetch("gainers", limit=100), []) or self._safe("Angel gainers", self.gainers.fetch, [])) if needs_india else [],

            losers=(self._safe("NSE losers", lambda: self.nse_movers.fetch("losers", limit=100), []) or self._safe("Angel losers", self.losers.fetch, [])) if needs_india else [],
        )
        if needs_india:
            name_pool = (
                brief.gainers[:15] + brief.losers[:15]
                + sorted(brief.gainers + brief.losers, key=lambda item: float(item.volume or 0), reverse=True)[:15]
            )
            self._safe("mover company names", lambda: self.company_names.enrich(name_pool), None)

        # ----------------------------------------------------
        # News
        # ----------------------------------------------------

        mover_pool = (
            brief.gainers[:10] + brief.losers[:10]
            + sorted(brief.gainers + brief.losers, key=lambda item: float(item.volume or 0), reverse=True)[:10]
        )
        mover_symbols = list(dict.fromkeys(item.name for item in mover_pool))
        ranked_indian = self._unique_articles(self._safe(
            "Indian market news",
            lambda: self.news_ranker.rank(self.news.collect(mover_symbols), limit=40),
            [],
        )) if needs_morning else []
        ranked_indian = self._safe(
            "India news summary enrichment",
            lambda: self.news_summaries.enrich(ranked_indian[:30], "Indian equities"),
            ranked_indian,
        )
        brief.indian_news = ranked_indian[:5]
        brief.indian_events = ranked_indian[5:10]

        # Backwards compatibility for existing consumers that read top_news.
        brief.top_news = brief.indian_news

        ranked_global = self._unique_articles(self._safe("US/global market news", lambda: self.global_news.collect(limit=30), [])) if needs_night else []
        ranked_global = self._safe(
            "global news summary enrichment",
            lambda: self.news_summaries.enrich(ranked_global[:30], "global equities and rates"),
            ranked_global,
        ) if needs_night else []
        brief.global_impact_news = ranked_global[:5]
        brief.us_events = ranked_global[5:10]
        ranked_crypto = self._unique_articles(self._safe("crypto market news", lambda: self.crypto_news.collect(limit=24), [])) if needs_night else []
        ranked_crypto = self._safe(
            "crypto news summary enrichment",
            lambda: self.news_summaries.enrich(ranked_crypto[:24], "crypto assets"),
            ranked_crypto,
        ) if needs_night else []
        brief.crypto_news = ranked_crypto[:10]
        (
            brief.global_indices,
            brief.indian_adrs,
            brief.commodities,
            brief.crypto,
        ) = self._safe("external market quotes", self.external_markets.fetch, ([], [], [], [])) if needs_external else ([], [], [], [])
        brief.us_gainers = self._safe("US gainers", lambda: self.us_movers.fetch("gainers"), []) if needs_night else []
        brief.us_losers = self._safe("US losers", lambda: self.us_movers.fetch("losers"), []) if needs_night else []
        brief.india_leaders = self._safe("India leaders", self.market_leaders.fetch_india, []) if needs_morning else []
        brief.us_mega_caps = self._safe("US mega caps", self.market_leaders.fetch_us, []) if needs_night else []
        brief.investor_flows = self._safe("FII/DII flows", self.institutional_flows.fetch, None) if (needs_morning or needs_afternoon) else None
        if needs_morning:
            flow_context = ""
            if brief.investor_flows:
                fii = brief.investor_flows.fii_net
                dii = brief.investor_flows.dii_net
                if fii is not None and dii is not None:
                    flow_context = f"Cash flow: FII {fii:+,.0f} Cr, DII {dii:+,.0f} Cr"
            (
                brief.today_bullish,
                brief.today_bearish,
                brief.week_bullish,
                brief.week_bearish,
                brief.growth_candidates,
            ) = self._safe(
                "broad NSE stock discovery",
                lambda: self.stock_discovery.analyze(
                    brief.gainers, brief.losers,
                    articles=brief.indian_news + brief.indian_events,
                    fii_dii_context=flow_context,
                ),
                ([], [], [], [], []),
            )
        if needs_night:
            global_articles = brief.global_impact_news + brief.us_events
            brief.us_move_reasons = self._move_reasons(
                brief.us_mega_caps,
                global_articles,
                {
                    "AAPL": ("apple",), "MSFT": ("microsoft",),
                    "GOOGL": ("alphabet", "google"), "AMZN": ("amazon",),
                    "NVDA": ("nvidia",), "META": ("meta platforms", "meta"),
                    "TSLA": ("tesla",),
                },
            )
            brief.crypto_move_reasons = self._move_reasons(
                brief.crypto,
                brief.crypto_news,
                {
                    "BITCOIN": ("bitcoin", " btc "),
                    "ETHEREUM": ("ethereum", "ether", " eth "),
                    "SOLANA": ("solana", " sol "),
                    "XRP": ("xrp", "ripple"),
                    "BNB": ("bnb", "binance coin", "binance"),
                    "DOGECOIN": ("dogecoin", " doge "),
                    "CARDANO": ("cardano", " ada "),
                    "CHAINLINK": ("chainlink", " link "),
                },
            )
        brief.macro_events = self._safe("official US macro calendar", self.macro_calendar.fetch, []) if (needs_morning or needs_night) else []
        if needs_night and brief.global_indices:
            positive = sum(item.percent_change > 0 for item in brief.global_indices)
            breadth = positive / len(brief.global_indices)
            average_change = sum(item.percent_change for item in brief.global_indices) / len(brief.global_indices)
            brief.health_score = round(breadth * 100)
            if breadth >= 0.60 and average_change > 0.15:
                brief.market_sentiment = "Bullish"
            elif breadth <= 0.40 and average_change < -0.15:
                brief.market_sentiment = "Bearish"
            else:
                brief.market_sentiment = "Neutral"
            brief.confidence = min(90, round(50 + abs(average_change) * 20))

        brief.top_ipos = self._safe("IPO GMP", lambda: self.ipo_gmp.fetch_top(limit=10), []) if needs_morning else []
        brief.fo_ban_symbols = self._safe("F&O ban list", self.premarket.fetch_fo_ban, []) if needs_morning else []
        brief.fo_ban_available = self.premarket.fo_ban_available
        brief.gift_nifty = self._safe("GIFT Nifty", self.premarket.fetch_gift_nifty, None) if needs_morning else None

        (
            brief.option_research,
            brief.option_research_failures,
        ) = self._safe("10 AM F&O research", self.options_radar.run, ([], [])) if needs_morning else ([], [])

        if needs_india and not any(item.name.upper() == "SENSEX" for item in brief.indices):
            sensex = self._safe("Sensex", self.sensex.fetch, None)
            if sensex:
                brief.indices.insert(1, sensex)

        # Health must be calculated before the AI receives its evidence.
        # Otherwise the narrative is built from the initial 0/Unknown values.
        if needs_india:
            brief = self._safe("market-health calculation", lambda: self.health.calculate(brief), brief)
        if needs_morning or needs_night:
            scope = "global" if needs_night else "india"
            brief.ai_summary, brief.ai_summary_source = self.summary_generator.generate(brief, scope=scope)
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
        """Cluster duplicate headlines and cap repeated coverage of one event."""
        unique = []
        fingerprints: list[set[str]] = []
        urls: set[str] = set()
        topic_counts: dict[str, int] = {}
        for article in articles:
            url = (article.url or "").split("?", 1)[0].rstrip("/").lower()
            text = f"{article.title or ''} {article.summary or ''}".lower()
            text = re.sub(r"foreign portfolio investors?|fpis?|fiis?", " fpi ", text)
            if "fpi" in text:
                text = re.sub(r"foreign investors?|turn buyers?(?: again)?|pour|\badd\b", " fpi_flow ", text)
            tokens = {
                token for token in re.findall(r"[a-z0-9]+", text)
                if len(token) > 2 and token not in {
                    "the", "and", "for", "with", "from", "into", "after", "amid",
                    "market", "markets", "stock", "stocks", "today", "says", "news",
                    "india", "indian", "this", "that", "over", "under", "their",
                }
            }
            if not tokens or (url and url in urls):
                continue
            topic = MorningBriefBuilder._headline_topic(text)
            # A professional digest should not become five rewrites of the same
            # Fed decision, tariff announcement or IPO story. Two perspectives
            # are useful; more displaces unrelated market-moving information.
            if topic and topic_counts.get(topic, 0) >= 2:
                continue
            duplicate = False
            for prior in fingerprints:
                intersection = len(tokens & prior)
                union = len(tokens | prior) or 1
                containment = intersection / max(1, min(len(tokens), len(prior)))
                if intersection / union >= 0.42 or (intersection >= 4 and containment >= 0.60):
                    duplicate = True
                    break
            if duplicate:
                continue
            fingerprints.append(tokens)
            if url:
                urls.add(url)
            if topic:
                topic_counts[topic] = topic_counts.get(topic, 0) + 1
            unique.append(article)
        return unique

    @staticmethod
    def _headline_topic(text: str) -> str:
        """Return a broad event family only when the wording is unambiguous."""
        topic_terms = {
            "fed-policy": (
                "federal reserve", "fomc", "fed chair", "fed decision",
                "fed rate", "warsh", "powell",
            ),
            "inflation-data": ("consumer price index", " cpi ", " pce ", "inflation report"),
            "jobs-data": ("payroll", "employment situation", "unemployment", "jobs report"),
            "tariffs": ("tariff", "trade levy", "trade war"),
            "oil-geopolitics": ("crude oil", "brent", "opec", "iran tensions", "west asia"),
            "foreign-flows": ("fpi_flow", "foreign portfolio", "fii inflow", "fpi inflow"),
            "ipo": (" ipo ", "public issue", "grey market premium"),
        }
        padded = f" {text.lower()} "
        return next(
            (topic for topic, terms in topic_terms.items() if any(term in padded for term in terms)),
            "",
        )

    @staticmethod
    def _move_reasons(quotes, articles, aliases: dict[str, tuple[str, ...]]) -> dict[str, str]:
        """Attach a reason only when a selected article explicitly names it."""
        reasons: dict[str, str] = {}
        for quote in quotes:
            key = str(quote.name).upper()
            terms = aliases.get(key, ())
            for article in articles:
                text = f" {article.title or ''} {article.summary or ''} ".lower()
                if terms and any(term in text for term in terms):
                    reason = " ".join((article.summary or article.title or "").split())
                    if len(reason) > 155:
                        reason = reason[:152].rsplit(" ", 1)[0] + "…"
                    reasons[key] = reason
                    break
        return reasons
