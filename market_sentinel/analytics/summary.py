"""
analytics/summary.py

Builds a human-readable market summary.

Author : Market Sentinel
Version : 0.4.0
"""

from market_sentinel.analytics.models import AssetAnalytics


class SummaryBuilder:

    @staticmethod
    def build(asset: AssetAnalytics) -> str:
        """
        Convert an AssetAnalytics object into a readable summary.
        """

        lines = []

        lines.append(f"📊 {asset.name} ({asset.symbol})")
        lines.append(f"Price : {asset.current_price:.2f}")

        lines.append(
            f"Daily : {asset.daily_change_pct:+.2f}%"
        )

        lines.append(
            f"Weekly : {asset.weekly_change_pct:+.2f}%"
        )

        lines.append(
            f"Monthly : {asset.monthly_change_pct:+.2f}%"
        )

        lines.append("")

        lines.append(f"Trend : {asset.trend.name}")

        if asset.trend_reason:
            lines.append(f"Reason : {asset.trend_reason}")

        lines.append("")

        lines.append(f"Momentum : {asset.momentum.name}")

        if asset.momentum_reason:
            lines.append(
                f"Reason : {asset.momentum_reason}"
            )

        if hasattr(asset, "volume_analysis"):

            volume = asset.volume_analysis

            lines.append("")
            lines.append(
                f"Volume : {volume.signal.name}"
            )

            lines.append(
                f"Activity : {volume.activity.name}"
            )

            lines.append(
                f"Confidence : {volume.confidence:.0f}%"
            )

        if asset.importance_score is not None:

            lines.append("")

            lines.append(
                f"Market Intelligence Score : "
                f"{asset.importance_score:.0f}/100"
            )

        return "\n".join(lines)