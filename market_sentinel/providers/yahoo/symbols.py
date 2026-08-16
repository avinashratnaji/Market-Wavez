"""
Yahoo Finance symbols.

This module contains all Yahoo Finance symbols monitored
by Market Sentinel.
"""

YAHOO_SYMBOLS = {
    "^NSEI": ("NIFTY 50", "NSE", "INDEX"),
    "GC=F": ("Gold", "COMEX", "COMMODITY"),
    "SI=F": ("Silver", "COMEX", "COMMODITY"),
    "CL=F": ("Crude Oil", "NYMEX", "COMMODITY"),
    "BTC-USD": ("Bitcoin", "CRYPTO", "CRYPTO"),
    "ETH-USD": ("Ethereum", "CRYPTO", "CRYPTO"),
    "INR=X": ("USD/INR", "FOREX", "FOREX"),
}