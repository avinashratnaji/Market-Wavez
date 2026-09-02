from datetime import datetime, timezone
import json
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from market_sentinel.briefs.ai_summary import MarketSummaryGenerator
from market_sentinel.briefs.models import MorningBrief
from market_sentinel.briefs.morning import MorningBriefBuilder
from market_sentinel.news.models import NewsArticle
from market_sentinel.providers.macro_calendar import UsMacroCalendarProvider
from market_sentinel.providers.angelone.models import StockSnapshot
from market_sentinel.providers.news.summary_enricher import NewsSummaryEnricher
from market_sentinel.providers.nse_movers import NseMoversProvider
from market_sentinel.providers.stock_discovery import StockDiscoveryProvider, _History
from market_sentinel.research.equity.premium import PremiumEquityAssessment
from market_sentinel.services.morning_brief_service import MorningBriefService
from market_sentinel.visuals.brief_card import BriefCardRenderer
from market_sentinel.research.options.models import OptionChainSnapshot, OptionContractQuote
from market_sentinel.research.options.providers import NseOptionChainProvider, SnapshotStore


def test_near_duplicate_fpi_headlines_are_clustered():
    articles = [
        NewsArticle("FPIs turn buyers again: foreign investors pour Rs 23,544 crore into Indian equities", "", "ET", "u1", score=70),
        NewsArticle("FIIs add ₹23,544 crore to India equities in August on earnings", "", "BS", "u2", score=68),
        NewsArticle("RBI announces a new payments framework", "", "RBI", "u3", score=65),
    ]

    result = MorningBriefBuilder._unique_articles(articles)

    assert len(result) == 2
    assert result[-1].source == "RBI"


def test_repeated_fed_coverage_is_capped_at_two_articles():
    articles = [
        NewsArticle("Warsh says Fed has more inflation work to do", "", "Reuters", "u1", score=80),
        NewsArticle("Fed chair Warsh puts inflation first", "", "CNBC", "u2", score=78),
        NewsArticle("Markets digest Warsh speech before Fed decision", "", "FT", "u3", score=76),
        NewsArticle("Nvidia unveils new data-centre chips", "", "Nvidia", "u4", score=70),
    ]

    result = MorningBriefBuilder._unique_articles(articles)

    assert len(result) == 3
    assert result[-1].source == "Nvidia"


def test_night_build_does_not_touch_india_or_options_providers():
    builder = MorningBriefBuilder()
    bomb = lambda: (_ for _ in ()).throw(AssertionError("unrelated provider called"))
    builder.indices.fetch = bomb
    builder.sectors.fetch = bomb
    builder.options_radar.run = bomb
    builder.ipo_gmp.fetch_top = bomb
    builder.global_news.collect = lambda limit=10: []
    builder.crypto_news.collect = lambda limit=5: []
    builder.external_markets.fetch = lambda: ([], [], [], [])
    builder.us_movers.fetch = lambda direction: []
    builder.market_leaders.fetch_us = lambda: []
    builder.macro_calendar.fetch = lambda: []

    brief = builder.build(window="night")

    assert brief.indices == []
    assert brief.option_research == []


def test_fed_parser_uses_only_meeting_rows(monkeypatch):
    html = """
    <div class="panel panel-default"><div class="panel-heading"><h4>2026 FOMC Meetings</h4></div>
      <div class="row fomc-meeting"><div class="fomc-meeting__month">September</div><div class="fomc-meeting__date">15-16*</div><div>Minutes released October 7</div></div>
      <div class="row fomc-meeting"><div class="fomc-meeting__month">October</div><div class="fomc-meeting__date">27-28</div></div>
    </div>
    """

    class Response:
        text = html
        def raise_for_status(self):
            return None

    monkeypatch.setattr("market_sentinel.providers.macro_calendar.requests.get", lambda *args, **kwargs: Response())
    events = UsMacroCalendarProvider()._fetch_fomc(datetime(2026, 8, 30, tzinfo=timezone.utc))

    assert [event.starts_at.day for event in events] == [16, 28]


def test_bea_parser_extracts_pce_and_gdp_only(monkeypatch):
    html = """
    <table>
      <tr><td>September 10 8:30 AM</td><td>News</td><td>Gross Domestic Product, 2nd Quarter 2026 (Third Estimate)</td></tr>
      <tr><td>September 30 8:30 AM</td><td>News</td><td>Personal Income and Outlays, August 2026</td></tr>
      <tr><td>October 2 8:30 AM</td><td>News</td><td>U.S. International Trade in Goods and Services</td></tr>
    </table>
    """

    class Response:
        text = html
        def raise_for_status(self):
            return None

    monkeypatch.setattr("market_sentinel.providers.macro_calendar.requests.get", lambda *args, **kwargs: Response())
    events = UsMacroCalendarProvider()._fetch_bea(datetime(2026, 8, 30, tzinfo=timezone.utc))

    assert [event.name for event in events] == ["U.S. GDP release", "PCE inflation / Personal Income and Outlays"]


def test_snapshot_store_uses_only_explicit_eod_files():
    # Avoid pytest's shared ``pytest-of-<username>`` folder. On Windows that
    # directory can retain an unusable ACL after an elevated/OneDrive run,
    # causing fixture setup to fail before this test executes.
    with TemporaryDirectory(prefix="market-wavez-snapshot-") as directory:
        store = SnapshotStore(Path(directory))
        quote = OptionContractQuote(100, "CE", 100)
        live = OptionChainSnapshot("DEMO", 100, "30-Sep-2026", datetime(2026, 8, 29, 10), (quote,), "test")
        eod = OptionChainSnapshot("DEMO", 100, "30-Sep-2026", datetime(2026, 8, 28, 16), (quote,), "test")
        store.save(live, kind="live")
        store.save(eod, kind="eod")

        result = store.previous_session_eod("DEMO")

        assert result is not None
        assert result.captured_at == eod.captured_at


def test_nse_chain_filters_every_contract_to_nearest_expiry():
    payload = {
        "records": {
            "underlyingValue": 100,
            "timestamp": "30-Aug-2026 10:00:00",
            "expiryDates": ["03-Sep-2026", "10-Sep-2026"],
            "data": [
                {"strikePrice": 100, "expiryDate": "03-Sep-2026", "CE": {"openInterest": 10, "expiryDate": "03-Sep-2026"}},
                {"strikePrice": 110, "expiryDate": "10-Sep-2026", "CE": {"openInterest": 999, "expiryDate": "10-Sep-2026"}},
            ],
        }
    }

    result = NseOptionChainProvider._parse("DEMO", payload)

    assert result.expiry == "03-Sep-2026"
    assert {quote.strike for quote in result.contracts} == {100}


def test_ai_summary_rejects_duplicate_bullets():
    with pytest.raises(ValueError, match="repeated"):
        MarketSummaryGenerator._validate(
            "• Federal Reserve inflation policy risk remains elevated today\n"
            "• Federal Reserve inflation policy risk remains elevated again\n"
            "• India breadth is neutral"
        )


def test_visual_card_plan_uses_section_titles_and_distinct_themes():
    brief = MorningBrief(
        generated_at=datetime(2026, 8, 30, 10),
        health_score=60,
        market_sentiment="Neutral",
        confidence=60,
        ai_summary="• Breadth is balanced\n• Confirm levels before acting",
        indian_news=[NewsArticle("India catalyst", "", "NSE", "https://nse.example")],
    )

    specs = BriefCardRenderer()._specs(brief, "morning")

    assert [(item.title, item.theme) for item in specs] == [
        ("AI-GROUNDED MARKET READ", "summary"),
        ("INDIA CATALYSTS · 1/2", "india_news"),
    ]
    assert all(item.title != "MARKET WAVEZ" for item in specs)


def test_visual_news_followups_are_scoped_to_requested_section():
    brief = MorningBrief(
        generated_at=datetime(2026, 8, 30, 21),
        health_score=60,
        market_sentiment="Neutral",
        confidence=60,
        global_impact_news=[NewsArticle("Fed event", "", "Federal Reserve", "https://fed.example")],
        crypto_news=[NewsArticle("Crypto event", "", "CoinDesk", "https://crypto.example")],
    )

    global_message = MorningBriefService._source_messages(brief, "night", "global_markets")[0]
    crypto_message = MorningBriefService._source_messages(brief, "night", "crypto")[0]
    movers_message = MorningBriefService._source_messages(brief, "night", "us_movers")[0]

    assert "Federal Reserve" in global_message and "CoinDesk" not in global_message
    assert "CoinDesk" in crypto_message and "Federal Reserve" not in crypto_message
    assert "MARKET NEWS" not in movers_message


def test_nse_mover_parser_supports_current_all_securities_fields():
    result = NseMoversProvider._snapshot({
        "symbol": "ATHERENERG",
        "ltp": "742.50",
        "net_price": "6.25",
        "open_price": "705.00",
        "high_price": "750.00",
        "low_price": "698.00",
        "prev_price": "698.83",
        "trade_quantity": "1876543",
    })

    assert result is not None
    assert result.name == "ATHERENERG"
    assert result.value == 742.5
    assert result.percent_change == 6.25
    assert result.volume == 1_876_543


def _stock(symbol: str, change: float, *, price: float = 150, company: str = "Example Limited") -> StockSnapshot:
    return StockSnapshot(
        name=symbol, exchange="NSE", token="", value=price, change=price * change / 100,
        percent_change=change, open=140, high=152, low=138, close=141,
        volume=2_000_000, updated_at=datetime(2026, 9, 2, 10), company_name=company,
    )


def test_stock_discovery_surfaces_momentum_and_reported_growth(monkeypatch):
    provider = StockDiscoveryProvider()
    ather = _stock("ATHERENERG", 6.2, company="Ather Energy Limited")
    weak = _stock("WEAKCO", -4.1, price=95, company="Weak Company")
    histories = {
        "ATHERENERG": _History(8.0, 19.0, 130.0, 120.0, 500_000),
        "WEAKCO": _History(-6.0, -12.0, 110.0, 120.0, 500_000),
    }
    monkeypatch.setattr(provider, "_histories", lambda stocks: histories)
    def assessments(stocks, histories, articles, fii_dii_context):
        return {
            "ATHERENERG": PremiumEquityAssessment(
                "ATHERENERG", "Ather Energy Limited", 78, 22, 18, 7, 14, 5, 12, 80,
                ("Sales 3Y growth 32.0%", "ROCE 18.0%"), (), (),
                ("Sales 3Y +32.0%", "Profit 3Y +28.0%"), "https://example.test/ather",
            ),
            "WEAKCO": PremiumEquityAssessment(
                "WEAKCO", "Weak Company", 42, 5, 5, 2, 3, 0, 42, 75,
                (), ("Elevated debt/equity (1.80x)",), (),
                ("Sales 3Y -8.0%",), "https://example.test/weak",
            ),
        }
    monkeypatch.setattr(provider.premium, "assess_many", assessments)

    today_up, today_down, week_up, week_down, growth = provider.analyze([ather], [weak])

    assert today_up[0].symbol == "ATHERENERG"
    assert today_down[0].symbol == "WEAKCO"
    assert week_up[0].symbol == "ATHERENERG"
    assert week_down[0].symbol == "WEAKCO"
    assert growth[0].growth_score == 22
    assert growth[0].quality_score == 18


def test_news_summary_enricher_removes_publisher_suffix_and_requires_context(monkeypatch):
    articles = [
        NewsArticle(
            "Ather rises after quarterly update - Example News",
            "Ather reported stronger deliveries while management retained its investment plan, giving investors new operating evidence rather than a price-only headline.",
            "Example News",
            "https://example.test/ather",
        ),
        NewsArticle("Market rises", "Market rises", "Wire", "https://example.test/weak"),
    ]
    monkeypatch.setattr(NewsSummaryEnricher, "_page_description", classmethod(lambda cls, url: ""))

    result = NewsSummaryEnricher().enrich(articles, "Indian equities")

    assert [item.title for item in result] == ["Ather rises after quarterly update"]
    assert "stronger deliveries" in result[0].summary


def test_source_followup_contains_summary_and_clickable_link():
    brief = MorningBrief(
        generated_at=datetime(2026, 9, 2, 10), health_score=60,
        market_sentiment="Neutral", confidence=60,
        indian_news=[NewsArticle(
            "Ather Energy reports stronger deliveries",
            "Quarterly deliveries rose and the company retained its operating plan, supplying a company-specific catalyst for the move.",
            "NSE filing", "https://example.test/filing",
        )],
    )

    message = MorningBriefService._source_messages(brief, "morning", "full")[0]

    assert "stronger deliveries" in message
    assert '<a href="https://example.test/filing">NSE filing</a>' in message
    assert "INDIA NEWS SOURCES" not in message
