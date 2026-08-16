"""
news/entity_extractor.py

Extracts companies, organizations and market entities
mentioned in a news article.

Author : Market Sentinel
"""

from __future__ import annotations
import re
from market_sentinel.news.models import NewsArticle


class EntityExtractor:

    ENTITIES = {

        # --------------------------------------------------
        # AI / Technology
        # --------------------------------------------------

        "OpenAI": [
            "openai",
        ],

        "Anthropic": [
            "anthropic",
        ],

        "Oracle": [
            "oracle",
        ],

        "IBM": [
            "ibm",
        ],

        "Cisco": [
            "cisco",
        ],

        "Adobe": [
            "adobe",
        ],

        "Salesforce": [
            "salesforce",
            "crm",
        ],

        "Palantir": [
            "palantir",
        ],

        "Snowflake": [
            "snowflake",
        ],

        "Netflix": [
            "netflix",
        ],

        # --------------------------------------------------
        # Semiconductor
        # --------------------------------------------------

        "TSMC": [
            "tsmc",
        ],

        "ASML": [
            "asml",
        ],

        "Micron": [
            "micron",
        ],

        "Arm": [
            "arm holdings",
        ],

        "Broadcom": [
            "broadcom",
        ],

        # --------------------------------------------------
        # Aerospace / Defense
        # --------------------------------------------------

        "SpaceX": [
            "spacex",
        ],

        "GE Aerospace": [
            "ge aerospace",
        ],

        "Boeing": [
            "boeing",
        ],

        "Lockheed Martin": [
            "lockheed",
        ],

        "Northrop Grumman": [
            "northrop",
        ],

        # --------------------------------------------------
        # EV / Energy
        # --------------------------------------------------

        "Rivian": [
            "rivian",
        ],

        "Lucid": [
            "lucid",
        ],

        "Bloom Energy": [
            "bloom energy",
        ],

        "Oklo": [
            "oklo",
        ],

        "First Solar": [
            "first solar",
        ],

        # --------------------------------------------------
        # Financials
        # --------------------------------------------------

        "Morgan Stanley": [
            "morgan stanley",
        ],

        "Goldman Sachs": [
            "goldman",
        ],

        "JPMorgan": [
            "jpmorgan",
            "jp morgan",
        ],

        "Citadel": [
            "citadel",
        ],

        "BlackRock": [
            "blackrock",
        ],

        # --------------------------------------------------
        # Crypto
        # --------------------------------------------------

        "Bitcoin": [
            "bitcoin",
            "btc",
        ],

        "Ethereum": [
            "ethereum",
            "eth",
        ],

        "Solana": [
            "solana",
            "sol",
        ],

        "Coinbase": [
            "coinbase",
        ],

        # --------------------------------------------------
        # Pharma
        # --------------------------------------------------

        "AbbVie": [
            "abbvie",
        ],

        "Johnson & Johnson": [
            "johnson & johnson",
            "jnj",
        ],

        "Novo Nordisk": [
            "novo nordisk",
        ],

        # --------------------------------------------------
        # India
        # --------------------------------------------------

        "Reliance": [
            "reliance",
        ],

        "TCS": [
            "tcs",
        ],

        "Infosys": [
            "infosys",
        ],

        "HCLTech": [
            "hcl",
        ],

        "Wipro": [
            "wipro",
        ],

        "Larsen & Toubro": [
            "l&t",
            "larsen",
        ],

        "Bharti Airtel": [
            "airtel",
        ],

        "ITC": [
            "itc",
        ],

        # --------------------------------------------------
        # US Tech
        # --------------------------------------------------

        "Microsoft": [
            "microsoft",
            "msft",
        ],

        "Google": [
            "google",
            "alphabet",
            "googl",
        ],

        "Amazon": [
            "amazon",
            "amzn",
        ],

        "Apple": [
            "apple",
            "aapl",
        ],

        "Meta": [
            "meta",
            "facebook",
        ],

        "Nvidia": [
            "nvidia",
            "nvda",
        ],

        "AMD": [
            "amd",
            "advanced micro devices",
        ],

        "Intel": [
            "intel",
        ],

        "Qualcomm": [
            "qualcomm",
        ],

        # --------------------------------------------------
        # Automobile
        # --------------------------------------------------

        "Tesla": [
            "tesla",
        ],

        "BYD": [
            "byd",
        ],

        "Toyota": [
            "toyota",
        ],

        "Hyundai": [
            "hyundai",
        ],

        # --------------------------------------------------
        # Finance
        # --------------------------------------------------

        "Visa": [
            "visa",
        ],

        "Mastercard": [
            "mastercard",
        ],

        "PayPal": [
            "paypal",
        ],

        "Berkshire Hathaway": [
            "berkshire",
        ],

        # --------------------------------------------------
        # Pharma
        # --------------------------------------------------

        "Eli Lilly": [
            "eli lilly",
        ],

        "Pfizer": [
            "pfizer",
        ],

        "Moderna": [
            "moderna",
        ],

        "Teva": [
            "teva",
        ],

        # --------------------------------------------------
        # Energy
        # --------------------------------------------------

        "Exxon": [
            "exxon",
        ],

        "Chevron": [
            "chevron",
        ],

        # --------------------------------------------------
        # India
        # --------------------------------------------------

        "Reliance": [
            "reliance",
        ],

        "TCS": [
            "tcs",
        ],

        "Infosys": [
            "infosys",
        ],

        "HDFC Bank": [
            "hdfc",
        ],

        "ICICI Bank": [
            "icici",
        ],

        "SBI": [
            "sbi",
        ],

        # --------------------------------------------------
        # Institutions
        # --------------------------------------------------

        "RBI": [
            "rbi",
        ],

        "SEBI": [
            "sebi",
        ],

        "Federal Reserve": [
            "fed",
            "federal reserve",
        ],

        "Bank of England": [
            "bank of england",
        ],
    }

    @classmethod
    def extract(
            cls,
            articles: list[NewsArticle],
    ) -> list[NewsArticle]:

        for article in articles:

            text = (
                    article.title + " " + article.summary
            ).lower()

            entities = set()

            for entity, aliases in cls.ENTITIES.items():

                for alias in aliases:

                    pattern = rf"\b{re.escape(alias.lower())}\b"

                    if re.search(pattern, text):
                        entities.add(entity)
                        break

            article.entities = sorted(entities)

        return articles