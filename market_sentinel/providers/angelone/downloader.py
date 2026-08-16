"""
downloader.py

Downloads and caches the Angel One Instrument Master.

Author : Market Sentinel
Version : 1.0.0
"""

from __future__ import annotations

import json
from pathlib import Path

import requests
from loguru import logger


INSTRUMENT_MASTER_URL = (
    "https://margincalculator.angelbroking.com/"
    "OpenAPI_File/files/OpenAPIScripMaster.json"
)

PROJECT_ROOT = Path(__file__).resolve().parents[3]

CACHE_DIR = PROJECT_ROOT / "data" / "instruments"

CACHE_FILE = CACHE_DIR / "instrument_master.json"


class InstrumentDownloader:

    def __init__(self) -> None:

        CACHE_DIR.mkdir(
            parents=True,
            exist_ok=True,
        )

    @property
    def cache_file(self) -> Path:
        return CACHE_FILE

    def exists(self) -> bool:
        return self.cache_file.exists()

    def download(self, force: bool = False) -> Path:
        """
        Download Instrument Master.

        Parameters
        ----------
        force
            Download even if cache exists.
        """

        if self.exists() and not force:

            logger.info(
                "Using cached Instrument Master."
            )

            return self.cache_file

        logger.info(
            "Downloading Angel One Instrument Master..."
        )

        response = requests.get(
            INSTRUMENT_MASTER_URL,
            timeout=60,
        )

        response.raise_for_status()

        data = response.json()

        with open(
            self.cache_file,
            "w",
            encoding="utf-8",
        ) as file:

            json.dump(
                data,
                file,
                ensure_ascii=False,
            )

        logger.success(
            "Downloaded {} instruments.",
            len(data),
        )

        return self.cache_file