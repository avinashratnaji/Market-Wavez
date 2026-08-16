"""BSE Sensex fallback when a broker's NSE instrument master omits it."""

from __future__ import annotations

from datetime import datetime

from loguru import logger

from market_sentinel.providers.angelone.models import IndexSnapshot


class SensexProvider:
    def fetch(self) -> IndexSnapshot | None:
        try:
            import yfinance as yf

            history = yf.download("^BSESN", period="5d", interval="1d", progress=False, auto_adjust=False)
            closes = history["Close"]
            if hasattr(closes, "columns"):
                closes = closes.iloc[:, 0]
            closes = closes.dropna()
            if closes.empty or len(closes) < 2:
                return None
            value, prior = float(closes.iloc[-1]), float(closes.iloc[-2])
            return IndexSnapshot(
                name="SENSEX", exchange="BSE", token="^BSESN", value=value,
                change=value - prior, percent_change=(value / prior - 1) * 100,
                open=value, high=value, low=value, close=value, volume=0,
                updated_at=datetime.now(),
            )
        except Exception as exc:
            logger.warning("Sensex fallback unavailable: {}", exc)
            return None
