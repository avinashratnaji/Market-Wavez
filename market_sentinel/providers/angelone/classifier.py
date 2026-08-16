"""
classifier.py

Enterprise Instrument Classification Engine.

Author : Market Sentinel
"""

from __future__ import annotations

from market_sentinel.providers.angelone.instruments import Instrument


ETF_KEYWORDS = (
    "ETF",
    "BEES",
    "LIQUID",
    "GOLD",
    "SILVER",
    "NIFTYBEES",
    "BANKBEES",
    "JUNIORBEES",
    "GOLDBEES",
    "SILVERBEES",
    "CPSEETF",
    "LIQUIDBEES"
)


class InstrumentClassifier:

    @staticmethod
    def is_index(inst: Instrument) -> bool:

        return inst.instrument_type == "AMXIDX"

    @staticmethod
    def is_future(inst: Instrument) -> bool:

        return inst.instrument_type.startswith("FUT")

    @staticmethod
    def is_option(inst: Instrument) -> bool:

        return inst.instrument_type.startswith("OPT")

    @staticmethod
    def is_etf(inst: Instrument) -> bool:

        symbol = inst.trading_symbol.upper()

        #
        # Common ETF names
        #

        if "BEES" in symbol:
            return True

        if symbol.endswith("ETF"):
            return True

        #
        # Known ETF prefixes
        #

        prefixes = (
            "NIFTYBEES",
            "BANKBEES",
            "JUNIORBEES",
            "GOLDBEES",
            "SILVERBEES",
            "LIQUIDBEES",
            "CPSEETF",
        )

        if symbol.startswith(prefixes):
            return True

        return False

    @staticmethod
    def is_stock(inst: Instrument) -> bool:

        if inst.exchange not in ("NSE", "BSE"):
            return False

        if not inst.trading_symbol.endswith("-EQ"):
            return False

        return True