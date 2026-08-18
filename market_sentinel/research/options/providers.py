"""NSE option-chain and EOD technical data adapters for private research."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

import requests

from market_sentinel.research.options.models import OptionChainSnapshot, OptionContractQuote, TechnicalSnapshot, WatchlistItem


class NseOptionChainProvider:
    HOME_URL = "https://www.nseindia.com"
    OPTION_CHAIN_URL = "https://www.nseindia.com/api/option-chain-equities"
    TIMEOUT_SECONDS = 15

    def fetch(self, symbol: str) -> OptionChainSnapshot:
        session = requests.Session()
        session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-IN,en;q=0.9",
            "Referer": "https://www.nseindia.com/option-chain",
        })
        session.get(self.HOME_URL, timeout=self.TIMEOUT_SECONDS)
        response = session.get(self.OPTION_CHAIN_URL, params={"symbol": symbol}, timeout=self.TIMEOUT_SECONDS)
        response.raise_for_status()
        return self._parse(symbol, response.json())

    @staticmethod
    def _parse(symbol: str, payload: dict[str, Any]) -> OptionChainSnapshot:
        records = payload.get("records") or {}
        rows = records.get("data") or []
        expiry_dates = records.get("expiryDates") or []
        spot = float(records.get("underlyingValue") or 0)
        # NSE sometimes omits underlyingValue outside an active session while
        # still returning the complete OI table.  OI remains valid evidence;
        # the scanner uses the separately sourced daily close for price/EMA.
        if not rows:
            raise ValueError(f"NSE option chain is incomplete for {symbol}")
        contracts: list[OptionContractQuote] = []
        for row in rows:
            strike = float(row.get("strikePrice") or 0)
            for option_type in ("CE", "PE"):
                leg = row.get(option_type)
                if not isinstance(leg, dict) or not strike:
                    continue
                contracts.append(OptionContractQuote(
                    strike=strike, option_type=option_type,
                    open_interest=int(float(leg.get("openInterest") or 0)),
                    change_in_open_interest=int(float(leg.get("changeinOpenInterest") or 0)),
                    volume=int(float(leg.get("totalTradedVolume") or 0)),
                    implied_volatility=_float_or_none(leg.get("impliedVolatility")),
                    last_price=_float_or_none(leg.get("lastPrice")),
                ))
        if not contracts:
            raise ValueError(f"NSE option chain has no contracts for {symbol}")
        return OptionChainSnapshot(
            symbol=symbol, spot_price=spot,
            expiry=str(expiry_dates[0]) if expiry_dates else "Nearest available",
            captured_at=_parse_timestamp(records.get("timestamp")),
            contracts=tuple(contracts), source="NSE option-chain",
        )


class YahooTechnicalProvider:
    """End-of-day measures used to add context to the NSE OI snapshot."""

    CHART_URL = "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"

    def fetch(self, item: WatchlistItem) -> TechnicalSnapshot:
        # Direct chart data avoids yfinance's process-local SQLite cache, which
        # can fail on Windows even when the underlying Yahoo quote is healthy.
        import pandas as pd

        response = requests.get(
            self.CHART_URL.format(symbol=item.yahoo_symbol),
            params={"range": "6mo", "interval": "1d", "events": "history"},
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=15,
        )
        response.raise_for_status()
        result = (response.json().get("chart") or {}).get("result") or []
        if not result:
            raise ValueError(f"Yahoo chart data unavailable for {item.symbol}")
        quote = (result[0].get("indicators") or {}).get("quote") or []
        if not quote:
            raise ValueError(f"Yahoo chart data has no daily bars for {item.symbol}")
        closes = [value for value in quote[0].get("close", []) if value is not None]
        volumes = [value for value in quote[0].get("volume", []) if value is not None]
        if len(closes) < 55 or len(volumes) < 20:
            raise ValueError(f"Not enough daily history for {item.symbol}")
        close = pd.Series(closes, dtype=float)
        volume = pd.Series(volumes, dtype=float)
        ema20 = close.ewm(span=20, adjust=False).mean().iloc[-1]
        ema50 = close.ewm(span=50, adjust=False).mean().iloc[-1]
        delta = close.diff()
        gain = delta.clip(lower=0).rolling(14).mean()
        loss = (-delta.clip(upper=0)).rolling(14).mean()
        rs = gain / loss.replace(0, float("nan"))
        rsi = 100 - (100 / (1 + rs.iloc[-1]))
        return TechnicalSnapshot(
            symbol=item.symbol, close=float(close.iloc[-1]), ema_20=float(ema20), ema_50=float(ema50),
            rsi_14=None if rsi != rsi else float(rsi), volume=float(volume.iloc[-1]),
            average_volume_20=float(volume.tail(20).mean()), captured_at=datetime.now(),
        )


class SnapshotStore:
    """Append-only evidence store so published analysis can be audited later."""

    def __init__(self, directory: Path | None = None) -> None:
        self.directory = directory or Path("data") / "research" / "options"

    def save(self, snapshot: OptionChainSnapshot) -> Path:
        target = self.directory / snapshot.captured_at.strftime("%Y-%m-%d")
        target.mkdir(parents=True, exist_ok=True)
        path = target / f"{snapshot.symbol}_{snapshot.captured_at.strftime('%H%M%S')}.json"
        payload = {
            "symbol": snapshot.symbol, "spot_price": snapshot.spot_price, "expiry": snapshot.expiry,
            "captured_at": snapshot.captured_at.isoformat(), "source": snapshot.source,
            "contracts": [
                {"strike": quote.strike, "type": quote.option_type, "oi": quote.open_interest,
                 "change_oi": quote.change_in_open_interest, "volume": quote.volume,
                 "iv": quote.implied_volatility, "last_price": quote.last_price}
                for quote in snapshot.contracts
            ],
        }
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return path

    def latest(self, symbol: str) -> OptionChainSnapshot | None:
        """Load the most recent persisted chain for an honest OI comparison."""
        if not self.directory.exists():
            return None
        candidates = sorted(self.directory.glob(f"**/{symbol}_*.json"), reverse=True)
        for path in candidates:
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
                contracts = tuple(
                    OptionContractQuote(
                        strike=float(row["strike"]), option_type=str(row["type"]),
                        open_interest=int(row.get("oi") or 0), change_in_open_interest=int(row.get("change_oi") or 0),
                        volume=int(row.get("volume") or 0), implied_volatility=_float_or_none(row.get("iv")),
                        last_price=_float_or_none(row.get("last_price")),
                    )
                    for row in payload.get("contracts", [])
                )
                if contracts:
                    return OptionChainSnapshot(
                        symbol=str(payload["symbol"]), spot_price=float(payload.get("spot_price") or 0),
                        expiry=str(payload.get("expiry") or "Unknown"),
                        captured_at=datetime.fromisoformat(payload["captured_at"]), contracts=contracts,
                        source=str(payload.get("source") or "stored option snapshot"),
                    )
            except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError):
                continue
        return None


def _parse_timestamp(value: Any) -> datetime:
    if isinstance(value, str):
        for fmt in ("%d-%b-%Y %H:%M:%S", "%d-%b-%Y %H:%M:%S %Z"):
            try:
                return datetime.strptime(value.strip(), fmt)
            except ValueError:
                continue
    return datetime.now()


def _float_or_none(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


class AngelOneOptionChainProvider:
    """Authenticated fallback when NSE's public endpoint is rate-limited.

    SmartAPI's FULL quote response differs slightly by account/API version;
    unknown fields are treated as unavailable rather than assumed to be zero.
    """

    def __init__(self) -> None:
        self._chain = None
        self._client = None

    def _option_chain(self):
        if self._chain is None:
            from market_sentinel.providers.angelone.option_chain import OptionChain
            self._chain = OptionChain()
        return self._chain

    def _api(self):
        if self._client is None:
            from market_sentinel.providers.angelone.client import AngelOneClient
            self._client = AngelOneClient().api
        return self._client

    def fetch(self, symbol: str, spot_price: float) -> OptionChainSnapshot:
        contracts = list(self._option_chain().contracts(symbol))
        if not contracts:
            raise ValueError(f"Angel One instrument master has no options for {symbol}")
        expiry = self._nearest_expiry(contracts)
        selected = [contract for contract in contracts if contract.expiry == expiry]
        # Keep the request light but retain a sufficiently broad zone around ATM.
        selected = [contract for contract in selected if abs(_normalised_strike(contract.strike, spot_price) - spot_price) <= spot_price * 0.12]
        # FULL quotes are requested only around ATM.  This is the part of the
        # chain relevant to a near-term setup and avoids tens of API batches
        # for far-out strikes that cannot form an actionable nearby zone.
        nearest_strikes = sorted(
            {_normalised_strike(contract.strike, spot_price) for contract in selected},
            key=lambda strike: abs(strike - spot_price),
        )[:25]
        selected = [
            contract for contract in selected
            if _normalised_strike(contract.strike, spot_price) in set(nearest_strikes)
        ]
        if not selected:
            raise ValueError(f"No near-ATM Angel One contracts for {symbol}")
        client = self._api()
        rows: list[dict[str, Any]] = []
        for start in range(0, len(selected), 50):
            chunk = selected[start:start + 50]
            exchange_tokens = {"NFO": [contract.token for contract in chunk]}
            response = client.getMarketData("FULL", exchange_tokens)
            if not response.get("status"):
                raise RuntimeError(f"Angel One FULL quote failed: {response.get('message', 'unknown error')}")
            rows.extend(response.get("data", {}).get("fetched", []) or [])
        by_token = {str(row.get("symbolToken") or row.get("token")): row for row in rows}
        quotes: list[OptionContractQuote] = []
        for contract in selected:
            row = by_token.get(str(contract.token))
            if not row:
                continue
            oi = _int_or_zero(row.get("opnInterest") or row.get("openInterest"))
            quotes.append(OptionContractQuote(
                strike=_normalised_strike(contract.strike, spot_price), option_type=contract.option_type,
                open_interest=oi,
                change_in_open_interest=_int_or_zero(row.get("opnInterestChange") or row.get("changeinOpenInterest")),
                volume=_int_or_zero(row.get("tradeVolume") or row.get("totalTradedVolume")),
                implied_volatility=_float_or_none(row.get("impliedVolatility")),
                last_price=_float_or_none(row.get("ltp")),
            ))
        if not quotes or not any(quote.open_interest for quote in quotes):
            raise ValueError(f"Angel One returned no OI values for {symbol}")
        return OptionChainSnapshot(symbol, spot_price, expiry, datetime.now(), tuple(quotes), "Angel One SmartAPI FULL quote")

    @staticmethod
    def _nearest_expiry(contracts: list[Any]) -> str:
        def key(contract: Any) -> tuple[datetime, str]:
            value = str(contract.expiry).upper().replace(" ", "")
            for fmt in ("%d%b%Y", "%d-%b-%Y", "%Y-%m-%d"):
                try:
                    return datetime.strptime(value, fmt), value
                except ValueError:
                    continue
            return datetime.max, value
        return min(contracts, key=key).expiry


def _normalised_strike(strike: float, spot_price: float) -> float:
    strike = float(strike)
    return strike / 100 if strike > spot_price * 10 else strike


def _int_or_zero(value: Any) -> int:
    try:
        return int(float(value or 0))
    except (TypeError, ValueError):
        return 0
