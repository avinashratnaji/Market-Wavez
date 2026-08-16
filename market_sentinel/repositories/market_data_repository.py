from sqlalchemy.exc import SQLAlchemyError

from market_sentinel.database.models.market_data import MarketData as ORMMarketData
from market_sentinel.database.session import SessionLocal
from market_sentinel.database.models.market_data import MarketData
from market_sentinel.utils.logger import logger
from sqlalchemy import select
from sqlalchemy import desc
from sqlalchemy import func
from sqlalchemy.orm import aliased

class MarketDataRepository:
    """
    Repository for MarketData persistence.
    """

    def save_many(self, records: list[MarketData]) -> int:
        """
        Save multiple market records in a single transaction.
        """
        session = SessionLocal()
        try:
            orm_records = [
                ORMMarketData(
                    symbol=item.symbol,
                    name=item.name,
                    exchange=item.exchange,
                    asset_type=item.asset_type,
                    price=item.price,
                    currency=item.currency,

                    current_volume=item.current_volume,
                    daily_change_pct=item.daily_change_pct,
                    weekly_change_pct=item.weekly_change_pct,
                    monthly_change_pct=item.monthly_change_pct,
                    average_volume_20d=item.average_volume_20d,

                    collected_at=item.collected_at,
                )
                for item in records
            ]
            session.add_all(orm_records)
            session.commit()
            logger.success(f"Saved {len(records)} records to PostgreSQL.")
            return len(records)

        except SQLAlchemyError as ex:
            session.rollback()
            logger.exception(ex)
            raise

        finally:
            session.close()

    def get_latest(self) -> list[ORMMarketData]:
        """
        Return all market records ordered by newest first.
        """
        session = SessionLocal()
        try:
            stmt = (
                select(ORMMarketData)
                .order_by(desc(ORMMarketData.collected_at))
            )
            return list(session.scalars(stmt))

        finally:
            session.close()

    def get_latest_by_symbol(self, symbol: str) -> ORMMarketData | None:
        """
        Return the latest record for one symbol.
        """
        session = SessionLocal()
        try:
            stmt = (
                select(ORMMarketData)
                .where(ORMMarketData.symbol == symbol)
                .order_by(desc(ORMMarketData.collected_at))
                .limit(1)
            )
            return session.scalar(stmt)

        finally:
            session.close()

    def get_latest_snapshot(self) -> list[ORMMarketData]:
        """
        Return the latest record for each market symbol.
        """
        session = SessionLocal()
        try:
            latest = (
                select(
                    ORMMarketData.symbol,
                    func.max(ORMMarketData.collected_at).label("latest_time")
                )
                .group_by(ORMMarketData.symbol)
                .subquery()
            )
            stmt = (
                select(ORMMarketData)
                .join(
                    latest,
                    (ORMMarketData.symbol == latest.c.symbol)
                    &
                    (ORMMarketData.collected_at == latest.c.latest_time)
                )
                .order_by(ORMMarketData.name)
            )
            return list(session.scalars(stmt))
        finally:
            session.close()

    def get_history(
            self,
            symbol: str,
            limit: int = 20,
    ) -> list[ORMMarketData]:
        session = SessionLocal()
        try:
            stmt = (
                select(ORMMarketData)
                .where(ORMMarketData.symbol == symbol)
                .order_by(desc(ORMMarketData.collected_at))
                .limit(limit)
            )
            return list(session.scalars(stmt))

        finally:
            session.close()

    def get_statistics(self, symbol: str):
        session = SessionLocal()
        try:
            stmt = (
                select(
                    func.count(ORMMarketData.id).label("records"),
                    func.max(ORMMarketData.price).label("highest"),
                    func.min(ORMMarketData.price).label("lowest"),
                    func.avg(ORMMarketData.price).label("average"),
                    func.max(ORMMarketData.collected_at).label("latest_time"),
                    func.min(ORMMarketData.collected_at).label("first_time"),
                )
                .where(ORMMarketData.symbol == symbol)
            )
            return session.execute(stmt).one()

        finally:
            session.close()