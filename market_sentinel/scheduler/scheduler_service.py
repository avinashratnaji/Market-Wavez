import time

from market_sentinel.config.settings import settings
from market_sentinel.services.market_service import MarketService
from market_sentinel.utils import logger


class SchedulerService:

    def __init__(self):

        self.market_service = MarketService()
        self.interval = settings.COLLECT_INTERVAL

    def start(self):

        logger.info("=" * 60)
        logger.info("Market Sentinel Scheduler Started")
        logger.info(f"Collection Interval : {self.interval} seconds")
        logger.info("Press Ctrl+C to stop.")
        logger.info("=" * 60)

        try:

            while True:

                logger.info("Starting market collection...")

                self.market_service.collect()

                logger.success("Collection completed.")

                logger.info(f"Sleeping for {self.interval} seconds...")

                time.sleep(self.interval)

        except KeyboardInterrupt:

            logger.warning("Scheduler stopped by user.")