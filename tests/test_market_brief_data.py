from datetime import datetime

from market_sentinel.briefs.models import IpoGmpSnapshot, InvestorFlowSnapshot, MorningBrief
from market_sentinel.news.models import NewsArticle
from market_sentinel.providers.market_brief_data import InstitutionalFlowProvider, IpoGmpProvider
from market_sentinel.providers.external_markets import ExternalMarketsProvider
from market_sentinel.telegram.morning import MorningFormatter


def test_flow_provider_reads_category_rows():
    class Row(dict):
        @property
        def index(self):
            return self.keys()

    # Unit-level validation of the net calculation path without an NSE call.
    assert InstitutionalFlowProvider._number(Row({"Net Value": "1,250.5"}), "Net Value") == 1250.5


def test_flow_provider_parses_nse_style_records():
    records = [
        {"category": "FII/FPI", "buyValue": "1,250.50", "sellValue": "1,675.25", "netValue": "-424.75"},
        {"category": "DII", "buyValue": "1,820.00", "sellValue": "1,208.00", "netValue": "612.00"},
    ]

    assert InstitutionalFlowProvider._values_from_records(records, ("fii", "fpi")) == (1250.5, 1675.25, -424.75)
    assert InstitutionalFlowProvider._values_from_records(records, ("dii",)) == (1820.0, 1208.0, 612.0)


def test_telegram_formats_flows_and_indicative_gmp():
    brief = MorningBrief(
        generated_at=datetime(2026, 8, 13, 9, 0),
        health_score=50,
        market_sentiment="Neutral",
        confidence=50,
        investor_flows=InvestorFlowSnapshot(
            datetime(2026, 8, 12),
            fii_buy=1_250.0,
            fii_sell=1_675.0,
            fii_net=-425.0,
            dii_buy=1_820.0,
            dii_sell=1_208.0,
            dii_net=612.0,
        ),
        top_ipos=[IpoGmpSnapshot(name="Example IPO", gmp=50, price_band_high=250)],
    )

    messages = MorningFormatter.format(brief)
    output = "\n".join(messages)

    assert "FII / FPI ACTIVITY" in output
    assert "-425.00 Cr" in output
    assert "NET SELLING" not in output
    assert "Gross Buy" in output
    assert "CURRENT OPEN IPOs" in output
    assert "informal" in output
    flow_message = next(message for message in messages if "INSTITUTIONAL FLOWS" in message)
    ipo_message = next(message for message in messages if "CURRENT OPEN IPOs" in message)
    assert "CURRENT OPEN IPOs" not in flow_message
    assert "FII / FPI ACTIVITY" not in ipo_message


def test_three_scheduled_brief_windows_route_data_to_the_right_panels():
    brief = MorningBrief(
        generated_at=datetime(2026, 8, 15, 8, 0),
        health_score=50,
        market_sentiment="Neutral",
        confidence=50,
        indian_news=[NewsArticle(
            title="India catalyst",
            summary="Market catalyst",
            source="ET",
            url="https://example.com/india-catalyst",
            score=60,
        )],
    )

    morning = "\n".join(MorningFormatter.format_window(brief, "morning"))
    afternoon = "\n".join(MorningFormatter.format_window(brief, "afternoon"))
    night = "\n".join(MorningFormatter.format_window(brief, "night"))

    assert "MORNING PRE-MARKET BRIEF" in morning
    assert "TOP 5 STORIES DRIVING THE SESSION" in morning
    assert "POST-MARKET BRIEF" in afternoon
    assert "GLOBAL MARKETS & CRYPTO BRIEF" in night


def test_investorgain_parser_keeps_only_open_ipos_and_ranks_gmp_percent():
    html = """
    <table><thead><tr><th>IPO Name</th><th>GMP</th><th>Price</th><th>Open Date</th><th>Close Date</th></tr></thead>
    <tbody>
      <tr><td>Lower GMP</td><td>₹20 (10%)</td><td>200</td><td>13-Aug</td><td>18-Aug</td></tr>
      <tr><td>Higher GMP</td><td>₹75 (30%)</td><td>250</td><td>14-Aug</td><td>19-Aug</td></tr>
      <tr><td>Closed IPO</td><td>₹100 (50%)</td><td>200</td><td>01-Aug</td><td>12-Aug</td></tr>
    </tbody></table>
    """

    ipos = IpoGmpProvider._parse_investorgain_html(html, today=datetime(2026, 8, 14))
    ipos.sort(key=lambda ipo: ipo.gmp_percent or 0, reverse=True)

    assert [ipo.name for ipo in ipos] == ["Higher GMP", "Lower GMP"]
    assert ipos[0].subscription_open == datetime(2026, 8, 14)


def test_india_and_global_news_use_matching_detailed_cards():
    article = NewsArticle(
        title="Crude oil moves after supply update",
        summary="Oil prices rose after a supply update with a potential India inflation impact.",
        source="Reuters",
        url="https://example.com/story",
        published_at=datetime(2026, 8, 14, 9, 30),
        score=82,
    )
    brief = MorningBrief(
        generated_at=datetime(2026, 8, 14, 11, 10),
        health_score=15,
        market_sentiment="Bearish",
        confidence=15,
        indian_news=[article],
        global_impact_news=[article],
    )

    messages = "\n".join(MorningFormatter.format(brief))

    assert "MARKET WAVES — INDIA MORNING BRIEF" in messages
    assert "GLOBAL MARKET NEWS" in messages
    # Both India and global stories must carry context; headline-only cards
    # are intentionally rejected as half-information.
    assert messages.count("• Summary:") == 2
    assert messages.count('href="https://example.com/story"') == 2


def test_bearish_sentiment_uses_a_bear_not_a_bull():
    brief = MorningBrief(
        generated_at=datetime(2026, 8, 14, 11, 10),
        health_score=15,
        market_sentiment="Bearish",
        confidence=15,
    )
    output = "\n".join(MorningFormatter.format(brief))
    assert "🐻 <b>Sentiment:</b> Bearish" in output
    assert "🐂 <b>Sentiment:</b> Bearish" not in output


def test_open_ipo_is_retained_over_a_weekend_for_the_next_trading_day():
    html = """
    <table><tr><th>IPO Name</th><th>GMP</th><th>Price</th><th>Open Date</th><th>Close Date</th></tr>
    <tr><td>Monday Close IPO</td><td>₹25</td><td>100</td><td>14-Aug</td><td>18-Aug</td></tr></table>
    """
    ipos = IpoGmpProvider._parse_investorgain_html(html, today=datetime(2026, 8, 15))
    assert [ipo.name for ipo in ipos] == ["Monday Close IPO"]


def test_nse_open_ipo_rows_are_visible_without_a_gmp_quote():
    html = """
    <table><tr><th>Company Name</th><th>Issue Start Date</th><th>Issue End Date</th><th>Status</th><th>Price Band</th></tr>
    <tr><td>Official SME IPO</td><td>14-Aug-2026</td><td>18-Aug-2026</td><td>Open</td><td>₹100 - ₹120</td></tr></table>
    """
    ipos = IpoGmpProvider._parse_nse_open_issues_html(html, datetime(2026, 8, 15))
    assert len(ipos) == 1
    assert ipos[0].name == "Official SME IPO"
    assert ipos[0].gmp is None
    assert ipos[0].price_band_high == 120.0


def test_nse_current_issue_api_keeps_an_sme_ipo_open_until_monday():
    payload = [{
        "companyName": "Live SME IPO Limited",
        "issueStartDate": "14-Aug-2026",
        "issueEndDate": "17-Aug-2026",
        "issuePrice": "₹100 - ₹120",
        "status": "Open",
    }]

    ipos = IpoGmpProvider._parse_nse_current_issues(payload, datetime(2026, 8, 15))

    assert len(ipos) == 1
    assert ipos[0].name == "Live SME IPO Limited"
    assert ipos[0].price_band_high == 120.0
    assert ipos[0].subscription_close == datetime(2026, 8, 17)


def test_ipowatch_parser_keeps_current_open_sme_ipos_over_the_weekend():
    html = """
    <table><tr><th>IPO Name</th><th>IPO GMP*</th><th>Trend</th><th>Price Band</th>
    <th>Est. Listing</th><th>Date</th><th>Type</th><th>Status</th></tr>
    <tr><td>Technocrats Plasma Systems</td><td>₹25</td><td>Up</td><td>₹132</td>
    <td>₹157</td><td>14-18 August</td><td>BSE SME</td><td>Open</td></tr>
    <tr><td>Credent Connect N Care</td><td>₹65</td><td>Up</td><td>₹189</td>
    <td>₹256</td><td>13-17 August</td><td>NSE SME</td><td>Open</td></tr>
    </table>
    """

    ipos = IpoGmpProvider._parse_ipowatch_html(html, datetime(2026, 8, 15))

    assert [ipo.name for ipo in ipos] == ["Technocrats Plasma Systems", "Credent Connect N Care"]
    assert ipos[0].gmp == 25
    assert ipos[1].subscription_close == datetime(2026, 8, 17)


def test_gmp_sources_are_merged_without_hiding_the_live_ipowatch_row():
    older = IpoGmpSnapshot(name="Live SME IPO", gmp=20, price_band_high=100, source="InvestorGain")
    live = IpoGmpSnapshot(
        name="Live SME IPO", gmp=25, price_band_high=100,
        updated_at=datetime(2026, 8, 15, 8, 15), source="IPO Watch",
    )

    merged = IpoGmpProvider._dedupe_gmp_sources([older], [live])

    assert len(merged) == 1
    assert merged[0].gmp == 25
    assert "IPO Watch" in merged[0].source


def test_live_ipo_date_formats_support_ordinal_and_month_first_ranges():
    ordinal = IpoGmpProvider._date_range("14th - 18th August", 2026)
    month_first = IpoGmpProvider._date_range("August 14-18", 2026)

    assert ordinal == (datetime(2026, 8, 14), datetime(2026, 8, 18))
    assert month_first == (datetime(2026, 8, 14), datetime(2026, 8, 18))


def test_indian_bullion_is_not_a_comex_inr_conversion():
    gold = ExternalMarketsProvider._parse_indian_gold("24K Gold /g ₹15,513 + 71")
    silver = ExternalMarketsProvider._parse_indian_silver("Silver /kg ₹2,50,000 1000 ₹2,50,000 ₹2,50,000")

    assert gold is not None and gold.name == "Gold 24K INDIA"
    assert gold.value == 155130
    assert silver is not None and silver.name == "Silver INDIA"
    assert silver.value == 250000


def test_global_heading_is_visible_when_no_event_qualifies():
    brief = MorningBrief(
        generated_at=datetime(2026, 8, 14, 11, 10),
        health_score=50,
        market_sentiment="Neutral",
        confidence=50,
    )

    output = "\n".join(MorningFormatter.format(brief))

    assert "GLOBAL MARKET NEWS" in output
    assert "No major market-moving stories were verified." in output
