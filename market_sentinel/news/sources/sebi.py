from market_sentinel.news.rss_provider import RSSNewsProvider


class SEBIProvider(RSSNewsProvider):

    rss_url = "https://www.sebi.gov.in/sebirss.xml"

    @property
    def name(self):
        return "SEBI"