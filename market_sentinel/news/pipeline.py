"""
news/pipeline.py

Orchestrates the complete news intelligence pipeline.

Pipeline:

ClassifiedNews
      │
      ▼
ScoringEngine
      │
      ▼
ReasoningEngine
      │
      ▼
NewsAnalysis
"""

from __future__ import annotations

from market_sentinel.news.classifier import ClassifiedNews
from market_sentinel.intelligence.news_analysis import NewsAnalysis
from market_sentinel.intelligence.reasoning import NewsReasoningEngine
from market_sentinel.intelligence.scoring import NewsScoringEngine


class NewsIntelligenceEngine:
    """
    Orchestrates news intelligence processing.
    """

    def __init__(self) -> None:
        self._scoring = NewsScoringEngine()
        self._reasoning = NewsReasoningEngine()

    def analyze(self, news: ClassifiedNews) -> NewsAnalysis:
        """
        Analyse a classified news event.
        """

        analysis = NewsAnalysis(news=news)

        self._scoring.calculate(analysis)

        self._reasoning.analyze(analysis)

        return analysis