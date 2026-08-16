"""
scheduler/jobs.py

Production Scheduler for Market Sentinel.

Schedules market collection, news collection and
Telegram broadcasts.

Author : Market Sentinel
Version : 1.0.0
"""

from __future__ import annotations

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from loguru import logger

from market_sentinel.config.settings import settings
from market_sentinel.services.market_service import MarketService
from market_sentinel.services.news_telegram_service import (
    NewsTelegramService,
)


class SchedulerService:
    """
    Production scheduler.

    Jobs
    ----
    • Market Collection
    • News Collection + Telegram Alerts
    """

    def __init__(self) -> None:

        self.scheduler = BlockingScheduler(
            timezone="Asia/Kolkata"
        )

        self.market_service = MarketService()
        self.news_service = NewsTelegramService()

    # ==========================================================
    # PUBLIC
    # ==========================================================

    def start(self) -> None:

        self._register_jobs()

        logger.info("=" * 70)
        logger.info("Market Sentinel Scheduler Started")
        logger.info("Timezone : Asia/Kolkata")
        logger.info("Scheduler : APScheduler")
        logger.info("=" * 70)

        try:

            self.scheduler.start()

        except (KeyboardInterrupt, SystemExit):

            logger.warning(
                "Scheduler stopped."
            )

    # ==========================================================
    # JOB REGISTRATION
    # ==========================================================

    def _register_jobs(self) -> None:

        interval = settings.COLLECT_INTERVAL

        # ------------------------------------------
        # Market Collection
        # ------------------------------------------

        self.scheduler.add_job(
            func=self.market_job,
            trigger=IntervalTrigger(
                seconds=interval,
            ),
            id="market_collection",
            name="Market Collection",
            max_instances=1,
            coalesce=True,
            replace_existing=True,
        )

        # ------------------------------------------
        # News Collection
        # ------------------------------------------

        self.scheduler.add_job(
            func=self.news_job,
            trigger=IntervalTrigger(
                seconds=interval,
            ),
            id="news_collection",
            name="News Collection",
            max_instances=1,
            coalesce=True,
            replace_existing=True,
        )

        logger.success(
            "Registered scheduler jobs."
        )

    # ==========================================================
    # JOBS
    # ==========================================================

    def market_job(self) -> None:

        logger.info(
            "Running Market Collection..."
        )

        try:

            self.market_service.collect()

            logger.success(
                "Market Collection completed."
            )

        except Exception:

            logger.exception(
                "Market Collection failed."
            )

    def news_job(self) -> None:

        logger.info(
            "Running News Collection..."
        )

        try:

            self.news_service.run()

            logger.success(
                "News Collection completed."
            )

        except Exception:

            logger.exception(
                "News Collection failed."
            )

    # ==========================================================
    # FUTURE JOBS
    # ==========================================================

    def register_morning_brief(
        self,
        hour: int = 9,
        minute: int = 0,
    ) -> None:

        self.scheduler.add_job(
            func=self._morning_brief,
            trigger=CronTrigger(
                hour=hour,
                minute=minute,
            ),
            id="morning_brief",
            replace_existing=True,
        )

    def register_closing_bell(
        self,
        hour: int = 16,
        minute: int = 15,
    ) -> None:

        self.scheduler.add_job(
            func=self._closing_bell,
            trigger=CronTrigger(
                hour=hour,
                minute=minute,
            ),
            id="closing_bell",
            replace_existing=True,
        )

    # ==========================================================
    # PLACEHOLDERS
    # ==========================================================

    @staticmethod
    def _morning_brief() -> None:

        logger.info(
            "Morning Brief job triggered."
        )

    @staticmethod
    def _closing_bell() -> None:

        logger.info(
            "Closing Bell job triggered."
        )