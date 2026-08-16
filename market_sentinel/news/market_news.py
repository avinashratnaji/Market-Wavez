from dataclasses import dataclass, field

from market_sentinel.news.models import NewsEvent


@dataclass(slots=True)
class MarketNewsEvent(NewsEvent):
    """
    News event enriched with market intelligence.
    """

    affected_symbols: list[str] = field(default_factory=list)

    affected_sectors: list[str] = field(default_factory=list)

    affected_indices: list[str] = field(default_factory=list)

    sentiment: str = "Neutral"

    confidence: float = 0.0