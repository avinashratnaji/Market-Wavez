"""
Volume Analyzer

Determines whether today's trading activity is
normal or unusual based on volume.

Version : 0.4.0
"""

from market_sentinel.analytics.enums import (
    VolumeSignal,
    ActivityType,
)

from market_sentinel.analytics.enums import (
    VolumeSignal,
    ActivityType,
    VolumeAnalysis,
)


class VolumeAnalyzer:

    @staticmethod
    def calculate(
        current_volume: float,
        average_volume: float,
        daily_change: float,
    ) -> VolumeAnalysis:

        if average_volume <= 0:
            ratio = 1.0
        else:
            ratio = current_volume / average_volume

        # -----------------------
        # Volume Signal
        # -----------------------

        if ratio >= 8:
            signal = VolumeSignal.UNUSUAL

        elif ratio >= 4:
            signal = VolumeSignal.VERY_HIGH

        elif ratio >= 2:
            signal = VolumeSignal.HIGH

        elif ratio >= 1.2:
            signal = VolumeSignal.ABOVE_AVERAGE

        else:
            signal = VolumeSignal.NORMAL

        # -----------------------
        # Activity
        # -----------------------

        if ratio >= 2 and daily_change > 2:
            activity = ActivityType.ACCUMULATION

        elif ratio >= 2 and daily_change < -2:
            activity = ActivityType.DISTRIBUTION

        elif ratio >= 4 and daily_change < -5:
            activity = ActivityType.PANIC_SELLING

        elif ratio >= 4 and daily_change > 5:
            activity = ActivityType.BREAKOUT

        else:
            activity = ActivityType.NORMAL

        confidence = min(ratio * 10, 100)

        reason = (
            f"Volume {ratio:.2f}x average "
            f"with price change {daily_change:.2f}%."
        )

        return VolumeAnalysis(
            ratio=ratio,
            signal=signal,
            activity=activity,
            confidence=confidence,
            reason=reason,
        )