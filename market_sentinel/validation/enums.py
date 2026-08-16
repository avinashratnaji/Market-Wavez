"""
validation/enums.py
Enumerations used by the validation engine.
Author : Market Sentinel
Version : 1.0.0
"""

from enum import Enum


class ValidationSeverity(Enum):
    """
    Severity of a validation finding.
    """

    INFO = "Info"
    WARNING = "Warning"
    ERROR = "Error"


class DataConfidence(Enum):
    """
    Confidence level of collected market data.
    """

    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"
    REJECTED = "Rejected"