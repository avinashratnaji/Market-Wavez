"""
news/provider.py

Base News Provider.

Author : Market Sentinel
"""

from __future__ import annotations

from abc import ABC
from abc import abstractmethod

from market_sentinel.news.models import NewsArticle


class NewsProvider(ABC):

    @abstractmethod
    def fetch(self) -> list[NewsArticle]:
        """
        Returns a list of news articles.
        """
        raise NotImplementedError