"""
providers/angelone/token_registry.py

Enterprise Instrument Registry.

Loads the complete Angel One Instrument Master and builds
multiple in-memory indexes for ultra-fast lookups.

Author : Market Sentinel
Version : 4.0.0
"""

from __future__ import annotations

import json
from collections import defaultdict

from loguru import logger

from market_sentinel.providers.angelone.classifier import (
    InstrumentClassifier,
)

from market_sentinel.providers.angelone.downloader import (
    InstrumentDownloader,
)

from market_sentinel.providers.angelone.instruments import (
    Instrument,
)

from market_sentinel.providers.angelone.normalizer import (
    SymbolNormalizer,
)


class TokenRegistry:

    def __init__(self):

        self._downloader = InstrumentDownloader()
        self._classifier = InstrumentClassifier()

        self._loaded = False

        # -------------------------------------------------
        # Primary Indexes
        # -------------------------------------------------

        self._by_token: dict[
            str,
            list[Instrument],
        ] = defaultdict(list)

        self._by_exchange_token: dict[
            tuple[str, str],
            Instrument,
        ] = {}

        self._by_exchange_symbol: dict[
            tuple[str, str],
            Instrument,
        ] = {}

        self._by_trading_symbol: dict[
            str,
            Instrument,
        ] = {}

        self._normalized: dict[
            str,
            Instrument,
        ] = {}

        # -------------------------------------------------
        # Category Cache
        # -------------------------------------------------

        self._stocks: list[Instrument] = []

        self._indices: list[Instrument] = []

        self._etfs: list[Instrument] = []

        self._futures: list[Instrument] = []

        self._options: list[Instrument] = []

        # -------------------------------------------------
        # Option Chain Cache
        # -------------------------------------------------

        self._expiries: dict[
            str,
            set[str],
        ] = defaultdict(set)

        self._contracts: dict[
            str,
            list[Instrument],
        ] = defaultdict(list)

        # -------------------------------------------------
        # Statistics
        # -------------------------------------------------

        self.total_loaded = 0
        self.total_stocks = 0
        self.total_indices = 0
        self.total_etfs = 0
        self.total_futures = 0
        self.total_options = 0

    # =====================================================
    # Statistics
    # =====================================================

    def _print_statistics(self):

        logger.success("Registry Loaded.")

        logger.info(
            "Total Instruments : {}",
            self.total_loaded,
        )

        logger.info(
            "Stocks : {}",
            self.total_stocks,
        )

        logger.info(
            "Indices : {}",
            self.total_indices,
        )

        logger.info(
            "ETFs : {}",
            self.total_etfs,
        )

        logger.info(
            "Futures : {}",
            self.total_futures,
        )

        logger.info(
            "Options : {}",
            self.total_options,
        )

    # =====================================================
    # Load Instrument Master
    # =====================================================

    def load(self):

        if self._loaded:
            return

        path = self._downloader.download()

        logger.info(
            "Loading Instrument Master..."
        )

        with open(
            path,
            "r",
            encoding="utf-8",
        ) as file:

            rows = json.load(file)

        logger.info(
            "Parsing {} instruments...",
            len(rows),
        )

        for row in rows:

            exchange = (
                row.get(
                    "exch_seg",
                    "",
                )
                .strip()
                .upper()
            )

            symbol = (
                row.get(
                    "name",
                    "",
                )
                .strip()
                .upper()
            )

            trading_symbol = (
                row.get(
                    "symbol",
                    "",
                )
                .strip()
                .upper()
            )

            token = str(
                row.get(
                    "token",
                    "",
                )
            ).strip()

            instrument_type = (
                row.get(
                    "instrumenttype",
                    "",
                )
                .strip()
                .upper()
            )

            expiry = (
                row.get(
                    "expiry",
                    "",
                )
                .strip()
            )

            strike = float(
                row.get(
                    "strike",
                    0,
                )
            )

            lot_size = int(
                row.get(
                    "lotsize",
                    1,
                )
            )

            tick_size = float(
                row.get(
                    "tick_size",
                    0,
                )
            )

            # ---------------------------------------------
            # Derived fields
            # ---------------------------------------------

            underlying = ""

            if instrument_type.startswith("OPT") or instrument_type.startswith("FUT"):
                underlying = symbol

            option_type = ""

            if instrument_type.startswith("OPT"):

                if trading_symbol.endswith("CE"):
                    option_type = "CE"

                elif trading_symbol.endswith("PE"):
                    option_type = "PE"

            instrument = Instrument(

                exchange=exchange,

                symbol=symbol,

                trading_symbol=trading_symbol,

                token=token,

                instrument_type=instrument_type,

                expiry=expiry,

                strike=strike,

                lot_size=lot_size,

                tick_size=tick_size,

                exchange_symbol=trading_symbol,

                underlying=underlying,

                option_type=option_type,
            )

            self._register(instrument)

        self._loaded = True

        self._print_statistics()

    # =====================================================
    # Register Instrument
    # =====================================================

    def _register(
        self,
        instrument: Instrument,
    ) -> None:

        self.total_loaded += 1

        # -------------------------------------------------
        # Token
        # -------------------------------------------------

        self._by_token[
            instrument.token
        ].append(
            instrument
        )

        # -------------------------------------------------
        # Exchange + Token
        # -------------------------------------------------

        self._by_exchange_token[
            (
                instrument.exchange,
                instrument.token,
            )
        ] = instrument

        # -------------------------------------------------
        # Exchange + Symbol
        # -------------------------------------------------

        if instrument.symbol:

            self._by_exchange_symbol[
                (
                    instrument.exchange,
                    instrument.symbol,
                )
            ] = instrument

        # -------------------------------------------------
        # Trading Symbol
        # -------------------------------------------------

        if instrument.trading_symbol:

            self._by_trading_symbol[
                instrument.trading_symbol
            ] = instrument

        # -------------------------------------------------
        # Normalized Lookup
        # -------------------------------------------------

        for text in (
            instrument.symbol,
            instrument.trading_symbol,
        ):

            normalized = SymbolNormalizer.normalize(
                text
            )

            if normalized:

                self._normalized.setdefault(
                    normalized,
                    instrument,
                )

        # -------------------------------------------------
        # Categories
        # -------------------------------------------------

        if self._classifier.is_index(
            instrument
        ):

            self._indices.append(
                instrument
            )

            self.total_indices += 1

        elif self._classifier.is_etf(
            instrument
        ):

            self._etfs.append(
                instrument
            )

            self.total_etfs += 1

        elif self._classifier.is_future(
            instrument
        ):

            self._futures.append(
                instrument
            )

            self.total_futures += 1

        elif self._classifier.is_option(
            instrument
        ):

            self._options.append(
                instrument
            )

            self.total_options += 1

        elif self._classifier.is_stock(
            instrument
        ):

            self._stocks.append(
                instrument
            )

            self.total_stocks += 1

        # -------------------------------------------------
        # Expiry Cache
        # -------------------------------------------------

        if (
            instrument.underlying
            and
            instrument.expiry
        ):

            self._expiries[
                instrument.underlying
            ].add(
                instrument.expiry
            )

        # -------------------------------------------------
        # Contract Cache
        # -------------------------------------------------

        if instrument.underlying:

            self._contracts[
                instrument.underlying
            ].append(
                instrument
            )

    # =====================================================
    # Lookup : Exchange + Token
    # =====================================================

    def find_by_exchange_token(
        self,
        exchange: str,
        token: str,
    ) -> Instrument | None:

        self.load()

        return self._by_exchange_token.get(
            (
                exchange.upper(),
                str(token),
            )
        )

    # =====================================================
    # Lookup : Exchange + Symbol
    # =====================================================

    def find(
        self,
        exchange: str,
        symbol: str,
    ) -> Instrument | None:

        self.load()

        return self._by_exchange_symbol.get(
            (
                exchange.upper(),
                symbol.upper(),
            )
        )

    # =====================================================
    # Lookup : Token
    # =====================================================

    def find_by_token(
        self,
        token: str,
    ) -> list[Instrument]:

        self.load()

        return self._by_token.get(
            str(token),
            [],
        )

    # =====================================================
    # Lookup : Trading Symbol
    # =====================================================

    def find_by_trading_symbol(
        self,
        trading_symbol: str,
    ) -> Instrument | None:

        self.load()

        return self._by_trading_symbol.get(
            trading_symbol.upper()
        )

    # =====================================================
    # Smart Lookup
    # =====================================================

    def lookup(
        self,
        text: str,
    ) -> Instrument | None:

        self.load()

        normalized = SymbolNormalizer.normalize(
            text
        )

        if not normalized:
            return None

        return self._normalized.get(
            normalized
        )

    # =====================================================
    # Search
    # =====================================================

    def search(
        self,
        text: str,
        limit: int = 25,
    ) -> list[Instrument]:

        self.load()

        if not text:
            return []

        query = SymbolNormalizer.normalize(
            text
        )

        results: list[Instrument] = []

        seen: set[str] = set()

        #
        # Exact match first
        #

        exact = self._normalized.get(
            query
        )

        if exact:

            results.append(exact)

            seen.add(
                exact.token
            )

        #
        # Partial search
        #

        for instruments in self._by_token.values():

            for instrument in instruments:

                if instrument.token in seen:
                    continue

                if (
                    query in SymbolNormalizer.normalize(
                        instrument.symbol
                    )
                    or
                    query in SymbolNormalizer.normalize(
                        instrument.trading_symbol
                    )
                ):

                    results.append(
                        instrument
                    )

                    seen.add(
                        instrument.token
                    )

                    if len(results) >= limit:
                        return results

        return results

    # =====================================================
    # Exists
    # =====================================================

    def exists(
        self,
        exchange: str,
        symbol: str,
    ) -> bool:

        return (
            self.find(
                exchange,
                symbol,
            )
            is not None
        )

    # =====================================================
    # Option Chain Helpers
    # =====================================================

    def contracts(
        self,
        underlying: str,
    ) -> tuple[Instrument, ...]:

        self.load()

        return tuple(

            self._contracts.get(
                underlying.upper(),
                [],
            )

        )

    def expiries(
        self,
        underlying: str,
    ) -> tuple[str, ...]:

        self.load()

        return tuple(

            sorted(

                self._expiries.get(
                    underlying.upper(),
                    set(),
                )

            )

        )

    # =====================================================
    # Statistics
    # =====================================================

    def count(self) -> int:

        self.load()

        return self.total_loaded

    # =====================================================
    # Categories
    # =====================================================

    def stocks(
        self,
    ) -> tuple[Instrument, ...]:

        self.load()

        return tuple(
            self._stocks
        )

    def indices(
        self,
    ) -> tuple[Instrument, ...]:

        self.load()

        return tuple(
            self._indices
        )

    def etfs(
        self,
    ) -> tuple[Instrument, ...]:

        self.load()

        return tuple(
            self._etfs
        )

    def futures(
        self,
    ) -> tuple[Instrument, ...]:

        self.load()

        return tuple(
            self._futures
        )

    def options(
        self,
    ) -> tuple[Instrument, ...]:

        self.load()

        return tuple(
            self._options
        )

    # =====================================================
    # All Instruments
    # =====================================================

    def all(
        self,
    ) -> tuple[Instrument, ...]:

        self.load()

        instruments: list[Instrument] = []

        for group in self._by_token.values():

            instruments.extend(
                group
            )

        return tuple(
            instruments
        )