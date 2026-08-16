"""
providers/angelone/option_chain.py

Enterprise Option Chain Engine.

Author : Market Sentinel
Version : 1.0.0
"""

from __future__ import annotations

from collections import defaultdict

from market_sentinel.providers.angelone.instruments import Instrument
from market_sentinel.providers.angelone.token_registry import TokenRegistry


class OptionChain:
    """
    Enterprise Option Chain Engine.
    """

    def __init__(self):

        self.registry = TokenRegistry()
        self.registry.load()

        #
        # Cached data
        #

        self._underlyings: dict[str, list[Instrument]] = defaultdict(list)
        self._expiries: dict[str, set[str]] = defaultdict(set)
        #
        # Option Chain Cache
        #
        # underlying
        #    -> expiry
        #        -> strike
        #            -> CE / PE
        #

        self._chains: dict[
            str,
            dict[
                str,
                dict[
                    float,
                    dict[str, Instrument]
                ]
            ]
        ] = defaultdict(
            lambda: defaultdict(
                lambda: defaultdict(dict)
            )
        )
        self._build_cache()

    # ==========================================================
    # Build Cache
    # ==========================================================

    def _build_cache(self):

        for contract in self.registry.options():

            if not contract.underlying:
                continue

            underlying = contract.underlying.upper()

            self._underlyings[
                underlying
            ].append(
                contract
            )

            if contract.expiry:

                self._expiries[
                    underlying
                ].add(
                    contract.expiry
                )

            #
            # Build option chain
            #

            if (
                    contract.expiry
                    and contract.option_type
            ):
                self._chains[
                    underlying
                ][
                    contract.expiry
                ][
                    contract.strike
                ][
                    contract.option_type
                ] = contract

    # ==========================================================
    # Underlyings
    # ==========================================================

    def underlyings(
        self,
    ) -> tuple[str, ...]:

        return tuple(

            sorted(

                self._underlyings.keys()

            )

        )

    # ==========================================================
    # Expiries
    # ==========================================================

    def expiries(
        self,
        underlying: str,
    ) -> tuple[str, ...]:

        return tuple(

            sorted(

                self._expiries.get(
                    underlying.upper(),
                    set(),
                )

            )

        )

    # ==========================================================
    # Contracts
    # ==========================================================

    def contracts(
        self,
        underlying: str,
    ) -> tuple[Instrument, ...]:

        return tuple(

            self._underlyings.get(
                underlying.upper(),
                [],
            )

        )

    # ==========================================================
    # Calls
    # ==========================================================

    def calls(
        self,
        underlying: str,
    ) -> tuple[Instrument, ...]:

        return tuple(

            contract

            for contract in self.contracts(
                underlying
            )

            if contract.option_type == "CE"

        )

    # ==========================================================
    # Puts
    # ==========================================================

    def puts(
        self,
        underlying: str,
    ) -> tuple[Instrument, ...]:

        return tuple(

            contract

            for contract in self.contracts(
                underlying
            )

            if contract.option_type == "PE"

        )

    # ==========================================================
    # Debug
    # ==========================================================

    def chain(
            self,
            underlying: str,
    ):

        return self._chains.get(
            underlying.upper(),
            {},
        )