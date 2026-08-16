"""
client.py

High-level Angel One client.

Responsibilities
----------------
- Authenticate automatically
- Expose SmartAPI
- Provide common API wrappers

Author : Market Sentinel
Version : 1.0.0
"""

from __future__ import annotations

from SmartApi import SmartConnect
from loguru import logger

from market_sentinel.providers.angelone.authentication import (
    AngelOneAuthentication,
)


class AngelOneClient:
    """
    High-level wrapper around SmartAPI.
    """

    def __init__(self) -> None:

        self._auth = AngelOneAuthentication()

        self._client: SmartConnect | None = None

    @property
    def api(self) -> SmartConnect:
        """
        Returns authenticated SmartAPI client.
        """

        if self._client is None:

            logger.info(
                "Authenticating with Angel One..."
            )

            self._client = self._auth.login()

        return self._client

    @property
    def feed_token(self) -> str:

        return self._auth.feed_token

    @property
    def jwt_token(self) -> str:

        return self._auth.jwt_token