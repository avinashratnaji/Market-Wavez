from datetime import datetime

from market_sentinel.research.options.models import (
    OptionChainSnapshot,
    OptionContractQuote,
    TechnicalSnapshot,
    WatchlistItem,
)
from market_sentinel.research.options.scanner import OptionResearchScanner


def test_bearish_setup_requires_converging_technical_and_oi_evidence():
    chain = OptionChainSnapshot(
        symbol="HEROMOTOCO", spot_price=5600, expiry="28-Aug-2026", captured_at=datetime.now(), source="NSE",
        contracts=(
            OptionContractQuote(5500, "CE", 100, 10),
            OptionContractQuote(5700, "CE", 900, 500),
            OptionContractQuote(5500, "PE", 300, -100),
            OptionContractQuote(5700, "PE", 100, -50),
        ),
    )
    technicals = TechnicalSnapshot("HEROMOTOCO", 5600, 5650, 5700, 42, 200, 100, datetime.now())
    item = WatchlistItem("HEROMOTOCO", "Hero MotoCorp", "HEROMOTOCO.NS", "HEROMOTOCO")

    result = OptionResearchScanner().analyze(item, chain, technicals)

    assert result.bias == "Bearish option-chain setup"
    assert result.resistance == 5700
    assert result.support == 5500
    assert "above 5,700.00" in result.invalidation
    assert result.confidence_score >= 70


def test_key_zones_never_treat_atm_strike_as_both_support_and_resistance():
    chain = OptionChainSnapshot(
        symbol="DEMO", spot_price=100, expiry="28-Aug-2026", captured_at=datetime.now(), source="NSE",
        contracts=(
            OptionContractQuote(100, "CE", 1000, 20), OptionContractQuote(110, "CE", 500, 10),
            OptionContractQuote(100, "PE", 1000, 20), OptionContractQuote(90, "PE", 500, 10),
        ),
    )
    technicals = TechnicalSnapshot("DEMO", 100, 95, 90, 55, 100, 100, datetime.now())
    item = WatchlistItem("DEMO", "Demo", "DEMO.NS", "DEMO")

    result = OptionResearchScanner().analyze(item, chain, technicals)

    assert result.support == 90
    assert result.resistance == 110
    assert result.support != result.resistance
