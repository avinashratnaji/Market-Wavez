"""
validation/engine.py
Validation engine for market data.
Executes all validation rules against a MarketData record.

Author : Market Sentinel
Version : 1.0.0
"""

from market_sentinel.database.models.market_data import MarketData
from market_sentinel.validation.models import ValidationResult
from market_sentinel.validation.rules import (
    ContractRollRule,
    ForexVolumeRule,
    InsufficientHistoryRule,
    PriceRule,
    SuspiciousVolumeRule,
)


class ValidationEngine:
    """
    Executes all validation rules for a MarketData record.
    """

    def __init__(self) -> None:
        self._rules = [
            PriceRule,
            ForexVolumeRule,
            InsufficientHistoryRule,
            ContractRollRule,
            SuspiciousVolumeRule,
        ]

    def validate(
            self,
            record: MarketData,
    ) -> ValidationResult:
        result = ValidationResult()

        for rule in self._rules:
            rule.validate(record, result)

        return result