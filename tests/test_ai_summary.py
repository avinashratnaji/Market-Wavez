from datetime import datetime

from market_sentinel.briefs.ai_summary import MarketSummaryGenerator
from market_sentinel.briefs.models import MorningBrief


def test_rules_based_summary_uses_brief_evidence():
    brief = MorningBrief(
        generated_at=datetime(2026, 8, 14, 9, 0),
        health_score=42,
        market_sentiment="Bearish",
        confidence=42,
    )

    text = MarketSummaryGenerator._fallback(brief)

    assert "Market tone: bearish" in text


def test_response_text_reads_responses_api_shape():
    payload = {
        "output": [
            {"content": [{"type": "output_text", "text": "• Evidence-based summary"}]}
        ]
    }

    assert MarketSummaryGenerator._response_text(payload) == "• Evidence-based summary"
