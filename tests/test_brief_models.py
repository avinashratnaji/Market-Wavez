from datetime import datetime

from market_sentinel.briefs.models import MorningBrief

brief = MorningBrief(
    generated_at=datetime.now(),
    health_score=82,
    market_sentiment="Bullish",
    confidence=84,
)

print()

print(brief)