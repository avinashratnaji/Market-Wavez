"""
Yahoo Finance mapper.

Converts raw Yahoo Finance responses into the
Market Sentinel MarketData model.
"""

from datetime import datetime

from market_sentinel.database.models.market_data import MarketData


class YahooMapper:
    """
    Maps Yahoo Finance responses to MarketData.
    """

    @staticmethod
    def to_market_data(
        symbol: str,
        name: str,
        exchange: str,
        asset_type: str,
        info,
        history,
    ) -> MarketData:
        """
        Convert Yahoo Finance data into a MarketData object.
        """

        # ---------------------------------
        # Current Price
        # ---------------------------------
        current_price = float(info["lastPrice"])

        # ---------------------------------
        # Current Volume
        # ---------------------------------
        current_volume = (
            float(history["Volume"].iloc[-1])
            if not history.empty
            else 0.0
        )

        # ---------------------------------
        # 20-Day Average Volume
        # ---------------------------------
        average_volume_20d = (
            float(history["Volume"].tail(20).mean())
            if not history.empty
            else 0.0
        )

        # ---------------------------------
        # Percentage Changes
        # ---------------------------------
        daily_change_pct = 0.0
        weekly_change_pct = 0.0
        monthly_change_pct = 0.0

        if len(history) >= 2:
            daily_change_pct = (
                (
                    history["Close"].iloc[-1]
                    - history["Close"].iloc[-2]
                )
                / history["Close"].iloc[-2]
            ) * 100

        if len(history) >= 6:
            weekly_change_pct = (
                (
                    history["Close"].iloc[-1]
                    - history["Close"].iloc[-6]
                )
                / history["Close"].iloc[-6]
            ) * 100

        if len(history) >= 20:
            monthly_change_pct = (
                (
                    history["Close"].iloc[-1]
                    - history["Close"].iloc[0]
                )
                / history["Close"].iloc[0]
            ) * 100

        return MarketData(
            symbol=symbol,
            name=name,
            exchange=exchange,
            asset_type=asset_type,
            price=float(current_price),
            currency=info.get("currency", ""),
            current_volume=float(current_volume),
            daily_change_pct=float(daily_change_pct),
            weekly_change_pct=float(weekly_change_pct),
            monthly_change_pct=float(monthly_change_pct),
            average_volume_20d=float(average_volume_20d),
            collected_at=datetime.utcnow(),
        )