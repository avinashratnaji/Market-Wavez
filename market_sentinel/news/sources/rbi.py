"""
Reserve Bank of India RSS Provider.
"""

from market_sentinel.news.rss_provider import RSSNewsProvider


class RBIProvider(RSSNewsProvider):
    """
    RBI RSS Provider.
    """

    rss_url = "https://rbi.org.in/pressreleases_rss.xml"

    @property
    def name(self) -> str:
        return "Reserve Bank of India"