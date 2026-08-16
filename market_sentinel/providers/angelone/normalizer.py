"""
providers/angelone/normalizer.py

Normalizes user-entered symbols into a canonical form.

Author : Market Sentinel
Version : 1.0.0
"""

from __future__ import annotations

import re


class SymbolNormalizer:
    """
    Converts different spellings into a normalized symbol.

    Example:
        Nifty 50
        nifty50
        NIFTY-50

    all become

        NIFTY50
    """

    @staticmethod
    def normalize(text: str) -> str:

        if not text:
            return ""

        text = text.upper().strip()

        # Remove spaces
        text = text.replace(" ", "")

        # Remove underscores
        text = text.replace("_", "")

        # Remove hyphens
        text = text.replace("-", "")

        # Remove special characters
        text = re.sub(r"[^A-Z0-9]", "", text)

        return text