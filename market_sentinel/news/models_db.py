"""
news/models_db.py

SQLAlchemy ORM models for news persistence.

These models represent the database schema and are kept
separate from the domain models (NewsEvent).

Author : Market Sentinel
Version: 1.1.0
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    DateTime,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from market_sentinel.database.base import Base


class NewsArticle(Base):
    """
    Database representation of a news article.
    """

    __tablename__ = "news_articles"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    provider: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    # Provider-specific ID (optional).
    # Not unique because many providers (e.g. RBI RSS)
    # don't supply one.
    provider_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    source: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    # URL is the real unique identifier.
    url: Mapped[str] = mapped_column(
        String(2048),
        nullable=False,
        unique=True,
    )

    title: Mapped[str] = mapped_column(
        String(1000),
        nullable=False,
    )

    summary: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    content: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    author: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    language: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="en",
    )

    category: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )

    subcategory: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    published_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    __table_args__ = (
        Index(
            "ix_news_provider_published",
            "provider",
            "published_at",
        ),
        Index(
            "ix_news_category_published",
            "category",
            "published_at",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"NewsArticle("
            f"id={self.id}, "
            f"provider='{self.provider}', "
            f"title='{self.title[:60]}...')"
        )