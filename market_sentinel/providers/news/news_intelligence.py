"""Event-aware selection for the Indian market-news briefing.

The keyword ranker remains the source of an article's importance score.  This
module is deliberately a second stage: it identifies the underlying event,
clusters overlapping coverage, and selects a varied set of stories for a
human-readable brief.  Keeping those responsibilities separate makes the
selection deterministic, explainable, and safe to tune without changing the
base scoring model.
"""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable

from market_sentinel.news.models import NewsArticle


@dataclass(frozen=True, slots=True)
class NewsAssessment:
    """Explainable intelligence attached to one selected news event."""

    article: NewsArticle
    event_type: str
    entities: tuple[str, ...]
    topics: tuple[str, ...]
    cluster_size: int
    corroborating_sources: tuple[str, ...]
    selection_score: float
    reasons: tuple[str, ...]


class NewsPortfolioSelector:
    """Turn scored articles into a diverse, event-level market-news brief."""

    VERSION = "1.0.0"
    SIMILARITY_THRESHOLD = 0.58
    _TOKEN_RE = re.compile(r"[a-z0-9]{3,}")

    # Terms that are useful for writing a headline but poor at distinguishing
    # two events.  Removing them makes title clustering much less noisy.
    _STOP_WORDS = frozenset({
        "after", "amid", "and", "are", "as", "at", "behind", "but",
        "data", "day", "for", "from", "gets", "has", "in", "india",
        "indian", "into", "is", "its", "market", "markets", "news",
        "on", "over", "says", "stock", "stocks", "that", "the", "to",
        "today", "up", "with", "will",
    })

    _EVENT_RULES: tuple[tuple[str, tuple[str, ...]], ...] = (
        ("MONETARY_POLICY", ("repo rate", "monetary policy", "rate cut", "rate hike")),
        ("REGULATION", ("sebi", "rbi", "regulation", "circular", "compliance", "margin norms")),
        ("EARNINGS", ("q1", "q2", "q3", "q4", "quarterly", "earnings", "profit", "revenue")),
        ("CORPORATE_ACTION", ("acquisition", "merger", "demerger", "stake", "buyback", "block deal", "bulk deal")),
        ("CAPITAL_MARKETS", ("ipo", "listing", "invit", "fpo", "fundraise")),
        ("MACRO", ("inflation", "cpi", "gdp", "rupee", "fii", "fpi", "trade deficit")),
        ("MARKET_MOVEMENT", ("sensex", "nifty", "market close", "market fall", "market rise")),
        ("COMMODITIES", ("crude", "oil", "gold", "silver", "commodity")),
    )

    _TOPIC_RULES: tuple[tuple[str, tuple[str, ...]], ...] = (
        ("banks", ("bank", "nbfc", "rbi", "repo rate")),
        ("regulation", ("sebi", "regulation", "circular", "margin")),
        ("equities", ("nifty", "sensex", "stock", "equity")),
        ("currency", ("rupee", "forex", "currency")),
        ("commodities", ("crude", "oil", "gold", "silver", "metal")),
        ("primary-market", ("ipo", "listing", "invit", "fpo")),
    )

    _ENTITY_RULES: tuple[tuple[str, tuple[str, ...]], ...] = (
        ("RBI", ("rbi", "reserve bank of india")),
        ("SEBI", ("sebi", "securities and exchange board")),
        ("NSE", ("nse", "national stock exchange")),
        ("BSE", ("bse", "bombay stock exchange")),
        ("NIFTY 50", ("nifty 50", "nifty50")),
        ("SENSEX", ("sensex",)),
        ("Jio Financial", ("jio financial",)),
    )

    def select(
        self,
        articles: Iterable[NewsArticle],
        limit: int = 10,
    ) -> list[NewsArticle]:
        """Return one high-quality representative per event cluster.

        The returned objects are the original ``NewsArticle`` instances, so
        existing Telegram renderers keep working unchanged.  Call
        :meth:`assess` when the explanation metadata is needed.
        """
        return [assessment.article for assessment in self.assess(articles, limit)]

    def assess(
        self,
        articles: Iterable[NewsArticle],
        limit: int = 10,
    ) -> list[NewsAssessment]:
        """Select articles and expose the reason for every selection."""
        if limit <= 0:
            return []

        clusters = self._cluster(list(articles))
        candidates = [self._representative(cluster) for cluster in clusters]
        candidates.sort(key=lambda item: self._candidate_key(item), reverse=True)

        selected: list[NewsAssessment] = []
        remaining = candidates.copy()
        event_counts: Counter[str] = Counter()
        topic_counts: Counter[str] = Counter()

        while remaining and len(selected) < limit:
            # Re-evaluate the remaining candidates after every choice.  This
            # is a small maximum-marginal-relevance step: a second macro item
            # can still win when it is materially more important, but it no
            # longer automatically crowds out an equally useful regulator,
            # earnings, or market-movement event.
            candidate = max(
                remaining,
                key=lambda item: self._adjusted_key(
                    item,
                    event_counts,
                    topic_counts,
                ),
            )
            remaining.remove(candidate)
            event_penalty = 4.0 * event_counts[candidate.event_type]
            topic_penalty = 1.5 * sum(topic_counts[topic] for topic in candidate.topics)
            adjusted = candidate.selection_score - event_penalty - topic_penalty
            candidate = NewsAssessment(
                article=candidate.article,
                event_type=candidate.event_type,
                entities=candidate.entities,
                topics=candidate.topics,
                cluster_size=candidate.cluster_size,
                corroborating_sources=candidate.corroborating_sources,
                selection_score=round(adjusted, 2),
                reasons=candidate.reasons + self._diversity_reasons(event_penalty, topic_penalty),
            )
            selected.append(candidate)
            event_counts[candidate.event_type] += 1
            topic_counts.update(candidate.topics)

        return selected

    def explain(self, article: NewsArticle, articles: Iterable[NewsArticle]) -> NewsAssessment | None:
        """Return the selected-event explanation for ``article``, if selected."""
        all_articles = list(articles)
        for assessment in self.assess(all_articles, limit=len(all_articles)):
            if assessment.article is article or assessment.article.url == article.url:
                return assessment
        return None

    def _cluster(self, articles: list[NewsArticle]) -> list[list[NewsArticle]]:
        clusters: list[list[NewsArticle]] = []
        for article in sorted(articles, key=self._article_key, reverse=True):
            for cluster in clusters:
                if self._same_event(article, cluster[0]):
                    cluster.append(article)
                    break
            else:
                clusters.append([article])
        return clusters

    def _representative(self, cluster: list[NewsArticle]) -> NewsAssessment:
        representative = max(cluster, key=self._article_key)
        source_names = tuple(sorted({article.source.strip() for article in cluster if article.source.strip()}))
        event_type = self._event_type(representative)
        topics = self._topics(representative)
        entities = self._entities(representative)
        corroboration_bonus = min(max(len(source_names) - 1, 0) * 2.0, 6.0)
        score = float(representative.score) + corroboration_bonus
        reasons = [f"base importance {representative.score}/100", f"classified as {event_type.lower().replace('_', ' ')}"]
        if corroboration_bonus:
            reasons.append(f"corroborated by {len(source_names)} independent sources")
        if entities:
            reasons.append("entities: " + ", ".join(entities))
        return NewsAssessment(
            article=representative,
            event_type=event_type,
            entities=entities,
            topics=topics,
            cluster_size=len(cluster),
            corroborating_sources=source_names,
            selection_score=score,
            reasons=tuple(reasons),
        )

    def _same_event(self, left: NewsArticle, right: NewsArticle) -> bool:
        if left.url and left.url == right.url:
            return True
        left_tokens = self._fingerprint(left)
        right_tokens = self._fingerprint(right)
        if not left_tokens or not right_tokens:
            return False
        overlap = len(left_tokens & right_tokens) / len(left_tokens | right_tokens)
        return overlap >= self.SIMILARITY_THRESHOLD

    def _fingerprint(self, article: NewsArticle) -> frozenset[str]:
        text = f"{article.title or ''} {article.summary or ''}".lower()
        return frozenset(token for token in self._TOKEN_RE.findall(text) if token not in self._STOP_WORDS)

    def _event_type(self, article: NewsArticle) -> str:
        text = self._text(article)
        for label, triggers in self._EVENT_RULES:
            if any(trigger in text for trigger in triggers):
                return label
        return "MARKET_NEWS"

    def _topics(self, article: NewsArticle) -> tuple[str, ...]:
        text = self._text(article)
        return tuple(label for label, triggers in self._TOPIC_RULES if any(trigger in text for trigger in triggers))

    def _entities(self, article: NewsArticle) -> tuple[str, ...]:
        text = self._text(article)
        return tuple(label for label, triggers in self._ENTITY_RULES if any(trigger in text for trigger in triggers))

    @staticmethod
    def _text(article: NewsArticle) -> str:
        return f"{article.title or ''} {article.summary or ''}".lower()

    @staticmethod
    def _article_key(article: NewsArticle) -> tuple[int, float]:
        published_at = article.published_at
        if published_at is None:
            timestamp = 0.0
        elif published_at.tzinfo is None:
            timestamp = published_at.replace(tzinfo=timezone.utc).timestamp()
        else:
            timestamp = published_at.astimezone(timezone.utc).timestamp()
        return article.score, timestamp

    @staticmethod
    def _candidate_key(candidate: NewsAssessment) -> tuple[float, float]:
        article = candidate.article
        published_at = article.published_at
        if published_at is None:
            timestamp = 0.0
        elif published_at.tzinfo is None:
            timestamp = published_at.replace(tzinfo=timezone.utc).timestamp()
        else:
            timestamp = published_at.astimezone(timezone.utc).timestamp()
        return candidate.selection_score, timestamp

    def _adjusted_key(
        self,
        candidate: NewsAssessment,
        event_counts: Counter[str],
        topic_counts: Counter[str],
    ) -> tuple[float, float]:
        event_penalty = 4.0 * event_counts[candidate.event_type]
        topic_penalty = 1.5 * sum(topic_counts[topic] for topic in candidate.topics)
        importance, recency = self._candidate_key(candidate)
        return importance - event_penalty - topic_penalty, recency

    @staticmethod
    def _diversity_reasons(event_penalty: float, topic_penalty: float) -> tuple[str, ...]:
        reasons: list[str] = []
        if event_penalty:
            reasons.append(f"event repetition adjustment -{event_penalty:g}")
        if topic_penalty:
            reasons.append(f"topic repetition adjustment -{topic_penalty:g}")
        return tuple(reasons)
