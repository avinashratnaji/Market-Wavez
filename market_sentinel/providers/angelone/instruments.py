"""
providers/angelone/instruments.py

Angel One Instrument Model

Author : Market Sentinel
Version : 3.0.0
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class Instrument:
    """
    Represents one instrument from the Angel One Instrument Master.
    """

    # -----------------------------
    # Identity
    # -----------------------------

    exchange: str
    symbol: str
    trading_symbol: str
    token: str

    # -----------------------------
    # Instrument Information
    # -----------------------------

    instrument_type: str

    expiry: str = ""

    strike: float = 0.0

    lot_size: int = 1

    tick_size: float = 0.0

    aliases: tuple[str, ...] = ()

    # -----------------------------
    # Future Expansion
    # -----------------------------

    isin: str = ""

    segment: str = ""

    option_type: str = ""

    underlying: str = ""

    exchange_symbol: str = ""

    # ==========================================================
    # Properties
    # ==========================================================

    @property
    def is_index(self) -> bool:
        return self.instrument_type == "AMXIDX"

    @property
    def is_stock(self) -> bool:
        return (
            self.exchange in ("NSE", "BSE")
            and self.instrument_type == ""
        )

    @property
    def is_future(self) -> bool:
        return self.instrument_type.startswith("FUT")

    @property
    def is_option(self) -> bool:
        return self.instrument_type.startswith("OPT")

    @property
    def is_etf(self) -> bool:

        name = self.trading_symbol.upper()

        return (
            "ETF" in name
            or "BEES" in name
            or "LIQUID" in name
        )

    @property
    def is_equity(self) -> bool:
        return self.is_stock

    @property
    def has_expiry(self) -> bool:
        return bool(self.expiry)

    @property
    def display_name(self) -> str:

        if self.trading_symbol:
            return self.trading_symbol

        return self.symbol