"""Rules-based option-chain interpretation for the private daily radar."""

from __future__ import annotations

from market_sentinel.research.options.models import OptionChainSnapshot, OptionResearchSetup, TechnicalSnapshot, WatchlistItem


class OptionResearchScanner:
    """Combine technical context and OI structure without issuing trade calls."""

    def analyze(
        self,
        item: WatchlistItem,
        chain: OptionChainSnapshot,
        technicals: TechnicalSnapshot,
        previous_chain: OptionChainSnapshot | None = None,
    ) -> OptionResearchSetup:
        calls = [quote for quote in chain.contracts if quote.option_type == "CE"]
        puts = [quote for quote in chain.contracts if quote.option_type == "PE"]
        total_call_oi = sum(quote.open_interest for quote in calls)
        total_put_oi = sum(quote.open_interest for quote in puts)
        pcr = total_put_oi / total_call_oi if total_call_oi else None
        close = technicals.close
        # A put OI wall is a potential support only below spot.  A call OI
        # wall is a potential resistance only above spot.  The ATM strike is
        # intentionally excluded: it is a pivot, not both support/resistance.
        call_wall = _highest_oi_strike([quote for quote in calls if quote.strike > close])
        put_base = _highest_oi_strike([quote for quote in puts if quote.strike < close])
        call_oi_change = sum(quote.change_in_open_interest for quote in calls)
        put_oi_change = sum(quote.change_in_open_interest for quote in puts)
        bearish_points = bullish_points = 0
        evidence: list[str] = []
        if technicals.ema_20 and close < technicals.ema_20:
            bearish_points += 1; evidence.append("Price is below EMA 20")
        elif technicals.ema_20:
            bullish_points += 1; evidence.append("Price is above EMA 20")
        if technicals.ema_20 and technicals.ema_50:
            if technicals.ema_20 < technicals.ema_50:
                bearish_points += 1; evidence.append("EMA 20 is below EMA 50")
            else:
                bullish_points += 1; evidence.append("EMA 20 is above EMA 50")
        if pcr is not None:
            if pcr < 0.85:
                bearish_points += 1; evidence.append(f"PCR is weak at {pcr:.2f}")
            elif pcr > 1.15:
                bullish_points += 1; evidence.append(f"PCR is supportive at {pcr:.2f}")
            else:
                evidence.append(f"PCR is balanced at {pcr:.2f}")
        if call_oi_change > put_oi_change and call_wall is not None:
            bearish_points += 1; evidence.append(f"Call OI build-up is concentrated near {call_wall:,.0f}")
        elif put_oi_change > call_oi_change and put_base is not None:
            bullish_points += 1; evidence.append(f"Put OI build-up is concentrated near {put_base:,.0f}")
        if technicals.relative_volume and technicals.relative_volume >= 1.25:
            evidence.append(f"Relative volume is elevated at {technicals.relative_volume:.2f}x")
        comparison = _oi_comparison(chain, previous_chain)
        if comparison:
            evidence.append(comparison)
        bonus = 5 if technicals.relative_volume and technicals.relative_volume >= 1.25 else 0
        if bearish_points >= bullish_points + 2:
            bias = "Bearish option-chain setup"; score = min(85, 45 + bearish_points * 10 + bonus)
            invalidation = _invalidation("above", call_wall or technicals.ema_20 or close)
        elif bullish_points >= bearish_points + 2:
            bias = "Bullish option-chain setup"; score = min(85, 45 + bullish_points * 10 + bonus)
            invalidation = _invalidation("below", put_base or technicals.ema_20 or close)
        else:
            bias = "Mixed option-chain setup"; score = 40 + min(20, max(bearish_points, bullish_points) * 5)
            invalidation = "No directional invalidation: market structure is mixed"
        return OptionResearchSetup(
            symbol=item.symbol, display_name=item.display_name, bias=bias, confidence_score=score,
            evidence=tuple(evidence[:6]) or ("No verified technical or OI evidence was available",),
            support=put_base, resistance=call_wall, pcr=pcr, invalidation=invalidation,
            risk_notes=(item.event_risk, "Expiry and broad-market reversals can invalidate OI interpretation"),
            market_events=(),
            source=f"{chain.source}; technicals: Yahoo Finance EOD", captured_at=chain.captured_at,
            data_quality="Verified snapshot" if calls and puts and technicals.ema_50 else "Partial data — interpret cautiously",
            technicals=technicals, chain=chain,
        )


def _highest_oi_strike(contracts):
    return max(contracts, key=lambda quote: quote.open_interest).strike if contracts else None


def _invalidation(direction: str, level: float) -> str:
    return f"Invalid if price closes {direction} {level:,.2f}"


def _oi_comparison(current: OptionChainSnapshot, previous: OptionChainSnapshot | None) -> str | None:
    if previous is None or previous.captured_at >= current.captured_at:
        return None
    prior = {(quote.strike, quote.option_type): quote.open_interest for quote in previous.contracts}
    if not prior:
        return None
    current_calls = sum(quote.open_interest for quote in current.contracts if quote.option_type == "CE")
    current_puts = sum(quote.open_interest for quote in current.contracts if quote.option_type == "PE")
    prior_calls = sum(value for (_, option_type), value in prior.items() if option_type == "CE")
    prior_puts = sum(value for (_, option_type), value in prior.items() if option_type == "PE")
    if not prior_calls or not prior_puts:
        return None
    call_change = (current_calls / prior_calls - 1) * 100
    put_change = (current_puts / prior_puts - 1) * 100
    return f"OI vs saved {previous.captured_at:%d %b %H:%M}: calls {call_change:+.1f}%, puts {put_change:+.1f}%"
