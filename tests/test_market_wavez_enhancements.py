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
        ("INDIA MARKET CATALYSTS", "india_news"),
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
    assert "NEWS SOURCES" not in movers_message
