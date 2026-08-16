"""
news/enums.py

Enumerations used by the News framework.

Author : Market Sentinel
Version: 1.0.0
"""

from enum import Enum


class NewsSentiment(Enum):
    """
    Overall sentiment of a news event.
    """

    BULLISH = "Bullish"
    BEARISH = "Bearish"
    NEUTRAL = "Neutral"


class MarketImpact(Enum):
    """
    Expected market impact.
    """

    VERY_HIGH = "Very High"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"
    MINIMAL = "Minimal"


class NewsImportance(Enum):
    """
    Editorial importance of a news event.
    """

    CRITICAL = 5
    HIGH = 4
    MEDIUM = 3
    LOW = 2
    TRIVIAL = 1


class EventStatus(Enum):
    """
    Processing status of a news event.
    """

    NEW = "New"
    CLASSIFIED = "Classified"
    SCORED = "Scored"
    PUBLISHED = "Published"

class NewsCategory(Enum):
    """
    Editorial classification.
    """
    EARNINGS = "Earnings"
    GUIDANCE = "Guidance"
    MERGER = "Merger"
    ACQUISITION = "Acquisition"
    BUYBACK = "Buyback"
    DIVIDEND = "Dividend"
    CAPEX = "Capex"
    DEBT = "Debt"
    PRODUCT = "Product"
    COMPETITION = "Competition"
    REGULATION = "Regulation"
    LEGAL = "Legal"
    MACRO = "Macro"
    GEOPOLITICS = "Geopolitics"
    COMMODITIES = "Commodities"
    FOREX = "Forex"
    BANKING = "Banking"
    TECHNOLOGY = "Technology"
    AUTOMOBILE = "Automobile"
    PHARMA = "Pharma"
    ENERGY = "Energy"
    DEFENCE = "Defence"
    ANALYST = "Analyst"
    TECHNICAL = "Technical"
    PERSONAL_FINANCE = "Personal Finance"
    GENERAL = "General"