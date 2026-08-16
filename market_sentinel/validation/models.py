"""
validation/models.py
Validation models used by the Validation Engine.
Author : Market Sentinel
Version : 1.0.0
"""

from dataclasses import dataclass, field
from market_sentinel.database.models.market_data import MarketData

from market_sentinel.validation.enums import (
    DataConfidence,
    ValidationSeverity,
)


@dataclass(slots=True)
class ValidationMessage:
    """
    Represents a single validation finding.
    """

    severity: ValidationSeverity
    title: str
    description: str


@dataclass(slots=True)
class ValidationResult:
    """
    Stores the validation outcome for a market record.
    """

    is_valid: bool = True

    confidence: DataConfidence = DataConfidence.HIGH

    messages: list[ValidationMessage] = field(default_factory=list)

    def add_info(
        self,
        title: str,
        description: str,
    ) -> None:
        self.messages.append(
            ValidationMessage(
                severity=ValidationSeverity.INFO,
                title=title,
                description=description,
            )
        )

    def add_warning(
        self,
        title: str,
        description: str,
    ) -> None:

        if self.confidence == DataConfidence.HIGH:
            self.confidence = DataConfidence.MEDIUM

        self.messages.append(
            ValidationMessage(
                severity=ValidationSeverity.WARNING,
                title=title,
                description=description,
            )
        )

    def add_error(
        self,
        title: str,
        description: str,
    ) -> None:

        self.is_valid = False
        self.confidence = DataConfidence.REJECTED

        self.messages.append(
            ValidationMessage(
                severity=ValidationSeverity.ERROR,
                title=title,
                description=description,
            )
        )

