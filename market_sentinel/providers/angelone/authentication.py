"""
authentication.py

Handles authentication with Angel One SmartAPI.

Responsibilities
----------------
- Generate TOTP
- Create SmartAPI session
- Retrieve JWT token
- Retrieve Refresh token
- Retrieve Feed token

Author : Market Sentinel
Version : 1.0.0
"""

from __future__ import annotations

import pyotp

from SmartApi import SmartConnect
from loguru import logger

from market_sentinel.config.settings import settings


class AngelOneAuthentication:
    """
    Handles SmartAPI authentication.
    """

    def __init__(self) -> None:

        self._client = SmartConnect(
            api_key=settings.ANGEL_API_KEY
        )

        self.jwt_token: str | None = None
        self.refresh_token: str | None = None
        self.feed_token: str | None = None

    @property
    def client(self) -> SmartConnect:
        return self._client

    def login(self) -> SmartConnect:
        """
        Login into SmartAPI.

        Returns
        -------
        SmartConnect
        """

        logger.info(
            "Logging into Angel One SmartAPI..."
        )

        otp = pyotp.TOTP(
            settings.ANGEL_TOTP_SECRET
        ).now()

        response = self._client.generateSession(
            clientCode=settings.ANGEL_CLIENT_ID,
            password=settings.ANGEL_PIN,
            totp=otp,
        )

        if not response.get("status"):

            raise RuntimeError(
                f"Angel One Login Failed : {response}"
            )

        data = response["data"]

        self.jwt_token = data["jwtToken"]

        self.refresh_token = data["refreshToken"]

        self.feed_token = self._client.getfeedToken()

        logger.success(
            "Angel One login successful."
        )

        return self._client