"""
Scores market importance.

Author : Market Sentinel
"""

from market_sentinel.news.enums import NewsCategory


class NewsImportanceScorer:

    SCORES = {

        NewsCategory.GEOPOLITICS: 98,

        NewsCategory.MACRO: 95,

        NewsCategory.EARNINGS: 94,

        NewsCategory.GUIDANCE: 93,

        NewsCategory.MERGER: 92,

        NewsCategory.ACQUISITION: 92,

        NewsCategory.BUYBACK: 91,

        NewsCategory.CAPEX: 90,

        NewsCategory.DEBT: 89,

        NewsCategory.COMPETITION: 87,

        NewsCategory.PRODUCT: 86,

        NewsCategory.REGULATION: 84,

        NewsCategory.LEGAL: 82,

        NewsCategory.COMMODITIES: 80,

        NewsCategory.FOREX: 78,

        NewsCategory.BANKING: 75,

        NewsCategory.TECHNOLOGY: 72,

        NewsCategory.AUTOMOBILE: 70,

        NewsCategory.PHARMA: 70,

        NewsCategory.ENERGY: 68,

        NewsCategory.DEFENCE: 68,

        NewsCategory.ANALYST: 55,

        NewsCategory.TECHNICAL: 50,

        NewsCategory.PERSONAL_FINANCE: 10,

        NewsCategory.GENERAL: 20,
    }

    def score(self, article):

        article.importance = self.SCORES.get(
            article.category,
            20,
        )

        return article