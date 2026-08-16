from market_sentinel.providers.news.indian_market_news import (
    IndianMarketNews,
)
from market_sentinel.providers.news.news_ranker import (
    NewsRanker,
)


def test_indian_news_feeds():

    print("\n")
    print("=" * 70)
    print("🇮🇳 MARKET SENTINEL - TOP 10 INDIAN MARKET NEWS")
    print("=" * 70)

    collector = IndianMarketNews()

    articles = collector.collect()

    print(f"\nRelevant Indian articles: {len(articles)}")

    assert articles

    ranker = NewsRanker()

    top_news = ranker.rank(
        articles,
        limit=10,
    )

    print("\n")
    print("=" * 70)
    print("🔥 TOP 10 INDIAN MARKET NEWS")
    print("=" * 70)

    for index, article in enumerate(
        top_news,
        start=1,
    ):

        print(f"\n{index}. {article.title}")
        print(f"   Source : {article.source}")
        print(f"   Score  : {article.score}/100")
        print(f"   URL    : {article.url}")

    assert len(top_news) <= 10