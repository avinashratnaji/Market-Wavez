from market_sentinel.news.rss_provider import RSSNewsProvider


class EconomicTimesProvider(RSSNewsProvider):

    rss_url = "..."

    @property
    def name(self):
        return "Economic Times"