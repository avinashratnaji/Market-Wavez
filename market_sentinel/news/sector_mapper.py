"""
news/sector_mapper.py

Maps extracted entities to market sectors.

Author : Market Sentinel
"""

from __future__ import annotations

from market_sentinel.news.models import NewsArticle


class SectorMapper:

    ENTITY_TO_SECTOR = {

        # -------------------------------------------------
        # Technology
        # -------------------------------------------------

        "Microsoft": "Technology",
        "Google": "Technology",
        "Amazon": "Technology",
        "Apple": "Technology",
        "Meta": "Technology",
        "Nvidia": "Technology",
        "AMD": "Technology",
        "Intel": "Technology",
        "Qualcomm": "Technology",
        "Broadcom": "Technology",
        "TSMC": "Technology",
        "ASML": "Technology",
        "Micron": "Technology",
        "Arm": "Technology",
        "Oracle": "Technology",
        "IBM": "Technology",
        "Cisco": "Technology",
        "Adobe": "Technology",
        "Salesforce": "Technology",
        "Snowflake": "Technology",
        "Palantir": "Technology",

        # -------------------------------------------------
        # Automobile
        # -------------------------------------------------

        "Tesla": "Automobile",
        "BYD": "Automobile",
        "Toyota": "Automobile",
        "Hyundai": "Automobile",

        # -------------------------------------------------
        # Banking / Finance
        # -------------------------------------------------

        "Visa": "Financial",
        "Mastercard": "Financial",
        "PayPal": "Financial",
        "JPMorgan": "Financial",
        "Morgan Stanley": "Financial",
        "Goldman Sachs": "Financial",
        "BlackRock": "Financial",
        "Citadel": "Financial",
        "HDFC Bank": "Financial",
        "ICICI Bank": "Financial",
        "SBI": "Financial",

        # -------------------------------------------------
        # Pharma
        # -------------------------------------------------

        "Pfizer": "Healthcare",
        "Moderna": "Healthcare",
        "Eli Lilly": "Healthcare",
        "Novo Nordisk": "Healthcare",
        "AbbVie": "Healthcare",
        "Teva": "Healthcare",

        # -------------------------------------------------
        # Energy
        # -------------------------------------------------

        "Exxon": "Energy",
        "Chevron": "Energy",
        "Bloom Energy": "Energy",

        # -------------------------------------------------
        # Telecom
        # -------------------------------------------------

        "Bharti Airtel": "Telecom",

        # -------------------------------------------------
        # Industrials
        # -------------------------------------------------

        "GE Aerospace": "Industrials",
        "Boeing": "Industrials",
        "Lockheed Martin": "Industrials",
        "Northrop Grumman": "Industrials",
        "Larsen & Toubro": "Industrials",

        # -------------------------------------------------
        # Crypto
        # -------------------------------------------------

        "Bitcoin": "Crypto",
        "Ethereum": "Crypto",
        "Solana": "Crypto",
        "Coinbase": "Crypto",
    }

    @classmethod
    def map(
        cls,
        articles: list[NewsArticle],
    ) -> list[NewsArticle]:

        for article in articles:

            sectors = set()

            for entity in article.entities:

                sector = cls.ENTITY_TO_SECTOR.get(entity)

                if sector:
                    sectors.add(sector)

            article.sectors = sorted(sectors)

        return articles