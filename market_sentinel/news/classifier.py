"""
news/classifier.py

Rule-based news classifier.

Author : Market Sentinel
"""

from __future__ import annotations

import re

from market_sentinel.news.enums import NewsCategory
from market_sentinel.news.models import NewsArticle


class NewsClassifier:

    RULES = [

        # =====================================================
        # Highest Priority
        # =====================================================

        (
            NewsCategory.EARNINGS,
            [
                "earnings",
                "quarterly results",
                "quarter results",
                "results",
                "guidance",
                "eps",
                "profit",
                "revenue",
            ],
        ),

        (
            NewsCategory.PERSONAL_FINANCE,
            [
                "mortgage",
                "refinancing",
                "refinance",
                "student loan",
                "personal loan",
                "home equity",
                "checking account",
                "credit card",
                "cd rates",
                "retirement",
                "retirees",
                "emergency loan",
                "newlyweds",
                "ramit sethi",
                "budget",
                "saving money",
                "financial advice",
            ],
        ),

        (
            NewsCategory.DEBT,
            [
                "debt",
                "borrowing",
                "bond issue",
                "credit facility",
            ],
        ),

        (
            NewsCategory.CAPEX,
            [
                "capex",
                "capital expenditure",
                "data center",
                "datacenter",
                "investment",
                "expansion",
            ],
        ),

        (
            NewsCategory.MERGER,
            [
                "merger",
                "merged",
                "merging",
            ],
        ),

        (
            NewsCategory.ACQUISITION,
            [
                "acquire",
                "acquired",
                "acquisition",
                "buyout",
                "takeover",
            ],
        ),

        (
            NewsCategory.BUYBACK,
            [
                "buyback",
                "share buyback",
            ],
        ),

        (
            NewsCategory.DIVIDEND,
            [
                "dividend",
                "special dividend",
            ],
        ),

        (
            NewsCategory.COMPETITION,
            [
                "rival",
                "market share",
                "competition",
                "competes",
            ],
        ),

        (
            NewsCategory.PRODUCT,
            [
                "launch",
                "launches",
                "launched",
                "introduces",
                "introduced",
                "unveils",
                "unveiled",
            ],
        ),

        (
            NewsCategory.REGULATION,
            [
                "sebi",
                "rbi",
                "regulation",
                "regulatory",
                "government policy",
            ],
        ),

        # =====================================================
        # Personal Finance
        # =====================================================

        (
            NewsCategory.PERSONAL_FINANCE,
            [
                "mortgage",
                "refinance",
                "student loan",
                "personal loan",
                "home equity",
                "checking account",
                "credit card",
                "cd rates",
                "retirement",
                "retirees",
                "loan lender",
                "loan lenders",
                "emergency loan",
                "emergency loans",
            ],
        ),

        # =====================================================
        # Macro
        # =====================================================

        (
            NewsCategory.MACRO,
            [
                "inflation",
                "cpi",
                "gdp",
                "repo rate",
                "interest rate",
                "fed",
                "fomc",
                "tariff",
            ],
        ),

        (
            NewsCategory.GEOPOLITICS,
            [
                "iran",
                "ukraine",
                "china",
                "war",
                "missile",
                "sanctions",
                "trump",
            ],
        ),

        (
            NewsCategory.COMMODITIES,
            [
                "gold",
                "silver",
                "crude oil",
                "oil",
                "gas",
                "copper",
            ],
        ),

        (
            NewsCategory.ANALYST,
            [
                "price target",
                "upgraded",
                "downgraded",
                "buy rating",
                "sell rating",
                "looks attractive",
                "prediction",
                "forecast",
                "doubles down",
            ],
        ),

        (
            NewsCategory.TECHNICAL,
            [
                "buy point",
                "buy points",
                "breakout",
                "support",
                "resistance",
                "moving average",
            ],
        ),

    ]

    # =========================================================

    @classmethod
    def classify(
        cls,
        articles: list[NewsArticle],
    ) -> list[NewsArticle]:

        for article in articles:

            text = (
                f"{article.title} {article.summary}"
            ).lower()

            article.category = NewsCategory.GENERAL

            for category, phrases in cls.RULES:

                matched = False

                for phrase in phrases:

                    pattern = (
                        rf"\b{re.escape(phrase)}\b"
                    )

                    if re.search(
                        pattern,
                        text,
                    ):

                        article.category = category
                        matched = True
                        break

                if matched:
                    break

        return articles