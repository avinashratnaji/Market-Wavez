"""
validation/rules.py
Validation rules for market data.
Each rule inspects a MarketData object and updates
the supplied ValidationResult.

Author : Market Sentinel
Version : 1.0.0
"""

from market_sentinel.database.models.market_data import MarketData
from market_sentinel.validation.models import ValidationResult


class PriceRule:
    """
    Validate market price.
    """

    @staticmethod
    def validate(
        record: MarketData,
        result: ValidationResult,
    ) -> None:

        if record.price <= 0:
            result.add_error(
                "Invalid Price",
                "Price must be greater than zero."
            )


class ForexVolumeRule:
    """
    Forex markets do not have centralized volume.
    """

    @staticmethod
    def validate(
        record: MarketData,
        result: ValidationResult,
    ) -> None:

        if (
            record.asset_type == "FOREX"
            and record.current_volume == 0
        ):
            result.add_info(
                "Forex Volume",
                "Zero volume is expected for spot Forex markets."
            )


class InsufficientHistoryRule:
    """
    Detect insufficient historical volume.
    """

    @staticmethod
    def validate(
        record: MarketData,
        result: ValidationResult,
    ) -> None:

        if (
            record.average_volume_20d == 0
            and record.current_volume > 0
        ):
            result.add_warning(
                "Insufficient History",
                "Average 20-day volume is unavailable."
            )


class ContractRollRule:
    """
    Detect possible futures contract rollover.
    """

    @staticmethod
    def validate(
        record: MarketData,
        result: ValidationResult,
    ) -> None:

        if record.average_volume_20d <= 0:
            return

        ratio = (
            record.current_volume /
            record.average_volume_20d
        )

        if ratio > 10:
            result.add_warning(
                "Possible Contract Roll",
                f"Volume is {ratio:.2f}× the 20-day average."
            )


class SuspiciousVolumeRule:
    """
    Detect suspicious volume spikes.
    """

    @staticmethod
    def validate(
        record: MarketData,
        result: ValidationResult,
    ) -> None:

        if record.average_volume_20d <= 0:
            return

        ratio = (
            record.current_volume /
            record.average_volume_20d
        )

        if (
            abs(record.daily_change_pct) < 0.10
            and ratio > 500
        ):
            result.add_warning(
                "Suspicious Volume",
                "Extremely high volume with almost no price movement."
            )