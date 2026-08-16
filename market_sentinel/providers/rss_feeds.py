"""
providers/rss_feeds.py

Production RSS Feed Registry.

Single source of truth for all RSS feeds used by
Market Sentinel.

Author : Market Sentinel
Version : 1.0.0
"""

from __future__ import annotations

# ==========================================================
# INDIA
# ==========================================================

INDIA = [

    # ------------------------------------------------------
    # Major Indian Financial News
    # ------------------------------------------------------

    # Economic Times
    "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms",

    # Moneycontrol
    # "https://www.moneycontrol.com/rss/business.xml",

    # Moneycontrol - Markets
    # "https://www.moneycontrol.com/rss/marketreports.xml",

    # Times of India - Business
    "https://timesofindia.indiatimes.com/rssfeeds/1898055.cms",

    # Business Standard
    # "https://www.business-standard.com/rss/home_page.rss",

    # Business Standard - Markets
    "https://www.business-standard.com/rss/markets-10601.rss",

    # ------------------------------------------------------
    # Indian Exchanges
    # ------------------------------------------------------

    # # NSE
    # "https://www.nseindia.com/api/rss?category=market",
    #
    # # BSE
    # "https://www.bseindia.com/rss/news.aspx",

    # ------------------------------------------------------
    # Indian Regulators
    # ------------------------------------------------------

    # RBI
    # "https://www.rbi.org.in/scripts/BS_PressReleaseDisplay.aspx?prid=0",

    # SEBI
    "https://www.sebi.gov.in/sebirss.xml",
]

# ==========================================================
# GLOBAL
# ==========================================================

GLOBAL = [

    # Reuters Business
    "https://feeds.reuters.com/reuters/businessNews",

    # Reuters World
    "https://feeds.reuters.com/Reuters/worldNews",

    # CNBC Top News
    "https://www.cnbc.com/id/100003114/device/rss/rss.html",

    # Yahoo Finance
    "https://finance.yahoo.com/rss",

    # MarketWatch
    "https://feeds.marketwatch.com/marketwatch/topstories/",

    # Investing.com
    "https://www.investing.com/rss/news.rss",
]

# ==========================================================
# CRYPTO
# ==========================================================

CRYPTO = [

    # CoinDesk
    "https://www.coindesk.com/arc/outboundfeeds/rss/",

    # CoinTelegraph
    "https://cointelegraph.com/rss",
]

# ==========================================================
# COMMODITIES
# ==========================================================

COMMODITIES = [

    # Investing Commodities
    "https://www.investing.com/rss/news_11.rss",
]

# ==========================================================
# ECONOMY
# ==========================================================

ECONOMY = [

    # IMF
    "https://www.imf.org/en/News/RSS",

    # World Bank
    "https://www.worldbank.org/en/news/all/rss",
]

# ==========================================================
# ALL FEEDS
# ==========================================================

ALL = (
    INDIA
    + GLOBAL
    + CRYPTO
    + COMMODITIES
    + ECONOMY
)

# ==========================================================
# HELPERS
# ==========================================================


def all_feeds() -> list[str]:
    """
    Return every configured RSS feed.
    """

    return list(dict.fromkeys(ALL))


def indian_feeds() -> list[str]:
    """
    Indian market feeds.
    """

    return INDIA.copy()


def global_feeds() -> list[str]:
    """
    Global market feeds.
    """

    return GLOBAL.copy()


def crypto_feeds() -> list[str]:
    """
    Crypto feeds.
    """

    return CRYPTO.copy()


def commodity_feeds() -> list[str]:
    """
    Commodity feeds.
    """

    return COMMODITIES.copy()


def economy_feeds() -> list[str]:
    """
    Economy feeds.
    """

    return ECONOMY.copy()